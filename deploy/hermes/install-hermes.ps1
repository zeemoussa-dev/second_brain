<#
.SYNOPSIS
  Installs Hermes, the agent runtime, on an offline Windows Server from this
  release folder.

.DESCRIPTION
  Run from an ELEVATED PowerShell, on the server, with the release folder
  already copied there. It reaches no network: every package it installs
  comes from the release's own vendor folder.

  It does what upstream's installer would do -- lay down the source, build
  the virtual environment, put the toolchain in place, register the services
  -- without the parts of it that need the internet (a git clone, PyPI, a
  Node download, a browser download). Upstream has no offline mode.

  It is safe to run again. Each step checks whether it is already done, so a
  run that failed halfway can simply be repeated, and an upgrade is this
  same script with a newer release.

.PARAMETER HermesHome
  Hermes' own directory: the source, the virtual environment, the config, the
  profiles, the sessions, the logs. Upstream nests all of it under one root
  and so does this.

.PARAMETER DashboardPort
  The port the HTTP API and web interface listen on. 9119 is Hermes' own
  default and what Second Brain expects.

.PARAMETER DashboardHost
  What the dashboard binds. 127.0.0.1 by default: it terminates no TLS and
  authenticates with a session token, so it is meant to be reached from the
  server itself, not from the network. See DEPLOY-HERMES.md before changing
  it.

.PARAMETER ModelBaseUrl
.PARAMETER ModelName
.PARAMETER ProviderName
  The inference endpoint Hermes should use. The API ROOT, no path after /v1 --
  Hermes appends /chat/completions itself. Not secret, so it can be passed
  here; the KEY cannot, and is a manual step.

.PARAMETER SecondBrainBackend
  An installed Second Brain's backend directory. When given (or found at the
  default location), the two lines it needs to find this Hermes are filled in
  for you, if they are still blank.

.EXAMPLE
  .\install-hermes.ps1 -ModelBaseUrl https://api.example.com/v1 -ModelName gpt-5
#>
[CmdletBinding()]
param(
    [string]$HermesHome = 'C:\Hermes',
    [int]$DashboardPort = 9119,
    [string]$DashboardHost = '127.0.0.1',
    [string]$ModelBaseUrl,
    [string]$ModelName,
    [string]$ProviderName = 'compass',
    [string]$SecondBrainBackend = 'C:\SecondBrain\src\backend',
    [string]$ServiceAccount
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }
# Where Hermes' own tooling looks for the interpreter it manages. Keeping the
# release's copy at that path means nothing has to be told about it.
$runtimeSubPath = '.hermes-runtime\python\cpython-3.11-windows-x86_64-none'

function Step([string]$text) { Write-Host "`n=== $text" -ForegroundColor Cyan }
function Note([string]$text) { Write-Host "    $text" -ForegroundColor DarkGray }
function Good([string]$text) { Write-Host "    $text" -ForegroundColor Green }

function Invoke-Native {
    # Fails on a program's EXIT CODE, not on whether it wrote to stderr: in
    # Windows PowerShell 5.1 with $ErrorActionPreference = 'Stop', one
    # ordinary pip progress line on stderr would otherwise abort the install.
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory)][string]$WhenItFails
    )
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe @Arguments
        if ($LASTEXITCODE -ne 0) { throw "$WhenItFails (exit code $LASTEXITCODE)" }
    } finally {
        $ErrorActionPreference = $previous
    }
}

# --------------------------------------------------------------------------
Step 'Checking this can work at all'
# Every one of these is cheaper to find now than after a half-install.
# --------------------------------------------------------------------------
$elevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
            ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $elevated) { throw 'Run this from an elevated PowerShell: it registers two Windows services and the service host''s DLLs.' }

# The release root is found by looking for what it must contain, not by
# counting directories up from here: this script is run from inside the
# release, and a wrong guess at that path is an install that fails on its
# first file copy.
$release = $here
while ($release -and -not (Test-Path (Join-Path $release 'vendor\wheels'))) {
    $parent = Split-Path $release -Parent
    if ($parent -eq $release) { break }
    $release = $parent
}
if (-not (Test-Path (Join-Path $release 'vendor\wheels'))) {
    throw "Could not find the release's vendor folder above $here. Run this script from inside the release folder it was shipped in."
}
$sourceInRelease = Join-Path $release 'app\hermes-agent'
if (-not (Test-Path (Join-Path $sourceInRelease 'pyproject.toml'))) {
    throw "The release at $release has no Hermes source in app\hermes-agent."
}
Note "release: $release"

# Windows still refuses paths over 260 characters to most programs, and
# Hermes' own tree is deep -- its translated documentation reaches 176
# characters on its own. Staged somewhere deep (a user profile, a redirected
# drive) the copy fails PART WAY THROUGH, file by file, which looks like a
# corrupt release rather than a path problem.
$longestInRelease = (Get-ChildItem -Recurse -File $release -ErrorAction SilentlyContinue |
    ForEach-Object { $_.FullName.Length } | Measure-Object -Maximum).Maximum
$longestInstalled = $longestInRelease - $sourceInRelease.Length + (Join-Path $HermesHome 'hermes-agent').Length
if ($longestInRelease -gt 250) {
    throw "This release is staged too deep: its longest path is $longestInRelease characters and Windows refuses over 260. Move the release folder somewhere short, like C:\Staging, and run this again."
}
if ($longestInstalled -gt 250) {
    throw "-HermesHome $HermesHome is too deep: the longest installed path would be $longestInstalled characters and Windows refuses over 260. Use a short root like C:\Hermes."
}
Note "deepest path once installed: $longestInstalled characters"

$holder = Get-NetTCPConnection -LocalPort $DashboardPort -State Listen -ErrorAction SilentlyContinue
if ($holder) {
    $owner = (Get-Process -Id $holder.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    throw "Port $DashboardPort is already held by $owner (pid $($holder.OwningProcess)). Stop it or pass -DashboardPort."
}
Good "elevated, release complete, port $DashboardPort free"

# --------------------------------------------------------------------------
Step 'Laying down Hermes'
# --------------------------------------------------------------------------
$source = Join-Path $HermesHome 'hermes-agent'
# Both created before the copy: `Copy-Item -Recurse <dir>\* <dest>` with a
# destination that does not exist yet treats it as a FILE, makes one out of
# the first item, and then fails on every directory with "container cannot
# be copied onto existing leaf item".
New-Item -ItemType Directory -Force -Path $HermesHome, $source | Out-Null
# The source is REPLACED on a re-run and the home is not: the home holds the
# profiles, the sessions and the config, which an upgrade must not touch.
# `venv` and the interpreter live inside the source directory on a normal
# Hermes install, so the copy is additive rather than a clean sweep.
Copy-Item -Recurse -Force (Join-Path $sourceInRelease '*') $source
Good "source at $source"

# --------------------------------------------------------------------------
Step 'Putting the Python runtime in place'
# Copied, not installed. Hermes manages its own interpreter, and that is what
# makes WAL mode usable: it refuses WAL on any SQLite below 3.51.3, and the
# newest python.org 3.11 installer ships 3.45. Nothing is installed
# machine-wide and nothing appears on PATH, so this cannot collide with the
# Python Second Brain uses on the same server.
# --------------------------------------------------------------------------
$runtimeInRelease = Join-Path $release "vendor\python-runtime\$(Split-Path $runtimeSubPath -Leaf)"
if (-not (Test-Path (Join-Path $runtimeInRelease 'python.exe'))) {
    throw "No Python runtime in the release at $runtimeInRelease."
}
$runtime = Join-Path $source $runtimeSubPath
if (-not (Test-Path (Join-Path $runtime 'python.exe'))) {
    $runtimeParent = Split-Path $runtime -Parent
    New-Item -ItemType Directory -Force -Path $runtimeParent | Out-Null
    # Copied INTO the parent, not onto the leaf: the release's own directory
    # is already named what Hermes looks for, so this lands exactly on
    # $runtime whether or not a half-finished copy is already there.
    Copy-Item -Recurse -Force $runtimeInRelease $runtimeParent
}
$runtimePython = Join-Path $runtime 'python.exe'
$facts = (& $runtimePython -c "import sys,sqlite3;print(sys.version.split()[0],sqlite3.sqlite_version)").Trim() -split '\s+'
Good "python $($facts[0]), sqlite $($facts[1])"

# uv, where Hermes expects to find it. Nothing on the serving path uses it,
# but `hermes setup`, `hermes update` and the lazy dependency installer all
# call ensure_uv(), which DOWNLOADS uv when it is missing -- a surprise
# network call on a box that has no network.
$uvInRelease = Join-Path $release 'vendor\bin\uv.exe'
if (Test-Path $uvInRelease) {
    New-Item -ItemType Directory -Force -Path (Join-Path $HermesHome 'bin') | Out-Null
    Copy-Item -Force $uvInRelease (Join-Path $HermesHome 'bin\uv.exe')
    Good "uv at $HermesHome\bin\uv.exe"
}

# --------------------------------------------------------------------------
Step 'Building the virtual environment from the vendored wheels'
# Built HERE rather than copied: one built on the release machine hard-codes
# that machine's user path and would not run under this account.
# --------------------------------------------------------------------------
$venv = Join-Path $source 'venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Invoke-Native $runtimePython @('-m', 'venv', $venv) 'Could not create the virtual environment.'
}
$wheels = Join-Path $release 'vendor\wheels'
# --no-index: never reach for a package index. On this machine there is none,
# and a silent attempt would hang for its timeout instead of failing.
Invoke-Native $venvPython @(
    '-m', 'pip', 'install', '--no-index', '--find-links', $wheels, '--upgrade', 'pip', 'setuptools', 'wheel'
) 'Could not install the build tools into the virtual environment.'
Invoke-Native $venvPython @(
    '-m', 'pip', 'install', '--no-index', '--find-links', $wheels, '-r', (Join-Path $release 'vendor\requirements-hermes.txt')
) 'Installing the Hermes packages failed.'

# Hermes itself, installed from the source tree so its `hermes` command and
# its own package metadata exist. --no-build-isolation is what makes this
# work offline: without it pip builds in a sandbox it has to populate from a
# package index, and there is none.
Invoke-Native $venvPython @(
    '-m', 'pip', 'install', '--no-index', '--find-links', $wheels,
    '--no-build-isolation', '--no-deps', '-e', $source
) 'Installing Hermes itself failed.'
Good "$((& $venvPython -m pip list 2>$null | Measure-Object -Line).Lines) packages installed"

# pywin32 ships the DLLs its service host needs inside site-packages, where
# nothing on the system path can find them. Without this step both services
# register cleanly and then fail to start with "the service did not respond
# in a timely fashion" -- which says nothing about a missing DLL. It also
# registers the event log source, which is the only place a service that
# cannot start has to say so.
$postInstall = Join-Path $venv 'Scripts\pywin32_postinstall.py'
if (Test-Path $postInstall) {
    Invoke-Native $venvPython @($postInstall, '-install', '-quiet') 'The pywin32 post-install step failed; the services would not start.'
    Good 'pywin32 service host registered'
}

# --------------------------------------------------------------------------
Step 'The Node toolchain'
# Not needed to serve. Needed by a handful of channels and tools that shell
# out to node, and impossible to fetch later, so it travels and is unpacked.
# --------------------------------------------------------------------------
$nodeInRelease = Join-Path $release 'vendor\node'
$nodeDir = Join-Path $HermesHome 'node'
if (Test-Path (Join-Path $nodeInRelease 'node.exe')) {
    if (-not (Test-Path (Join-Path $nodeDir 'node.exe'))) {
        Copy-Item -Recurse -Force $nodeInRelease $nodeDir
    }
    Good "node at $nodeDir"
} else {
    $nodeDir = $null
    Note 'no node toolchain in this release; tools that shell out to node will not work'
}

# --------------------------------------------------------------------------
Step 'Writing this install''s settings'
# --------------------------------------------------------------------------
$envFile = Join-Path $HermesHome '.env'
if (Test-Path $envFile) {
    Note '.env already exists; leaving it alone'
} else {
    # Upstream's own annotated template, which is what a normal install
    # starts from too: 500 lines of commented examples, nothing set.
    Copy-Item (Join-Path $source '.env.example') $envFile
    $keyEnv = 'HERMES_' + ($ProviderName.ToUpperInvariant() -replace '[^A-Z0-9]', '_') + '_API_KEY'
    Add-Content $envFile @"

# ---------------------------------------------------------------------------
# Added by install-hermes.ps1 on $(Get-Date -Format 'yyyy-MM-dd').
# ---------------------------------------------------------------------------
# The inference key. config.yaml names this variable and holds no secret of
# its own, so this file is the only one to protect.
$keyEnv=

# Node is told to trust what Windows trusts. On a corporate network that
# intercepts TLS, node otherwise refuses every HTTPS call with
# UNABLE_TO_GET_ISSUER_CERT_LOCALLY while a browser on the same machine is
# fine, because it ships its own certificate list.
NODE_OPTIONS=--use-system-ca
"@
    Good "wrote $envFile"
    Note "fill in $keyEnv before starting the services"
}

$configFile = Join-Path $HermesHome 'config.yaml'
if (Test-Path $configFile) {
    Note 'config.yaml already exists; leaving it alone'
} else {
    $keyEnv = 'HERMES_' + ($ProviderName.ToUpperInvariant() -replace '[^A-Z0-9]', '_') + '_API_KEY'
    $template = Get-Content (Join-Path $here 'config.yaml.template') -Raw
    $template = $template.Replace('__PROVIDER_NAME__', $ProviderName).
                          Replace('__KEY_ENV__', $keyEnv).
                          Replace('__MODEL__', $(if ($ModelName) { $ModelName } else { '<the model name>' })).
                          Replace('__MODEL_BASE_URL__', $(if ($ModelBaseUrl) { $ModelBaseUrl } else { '<the API root, no /chat/completions>' }))
    Set-Content -Path $configFile -Value $template -Encoding UTF8
    Good "wrote $configFile"
    if (-not $ModelBaseUrl -or -not $ModelName) { Note 'fill in the model and its base URL there' }
}

# Machine-wide, so `hermes` run by hand from any account on this server finds
# the same home the services use. A service account's own %LOCALAPPDATA% --
# the default -- is a directory under C:\Windows nobody would look in.
[Environment]::SetEnvironmentVariable('HERMES_HOME', $HermesHome, 'Machine')
$env:HERMES_HOME = $HermesHome
Good "HERMES_HOME=$HermesHome (machine-wide)"

# --------------------------------------------------------------------------
Step 'Registering the Windows services'
# Two, because Hermes is two processes: the gateway runs the work, the
# dashboard answers HTTP. Starting one does not start the other.
# --------------------------------------------------------------------------
$deployDir = Join-Path $HermesHome 'deploy'
New-Item -ItemType Directory -Force -Path $deployDir | Out-Null
Copy-Item -Force (Join-Path $here 'hermes_service.py') $deployDir
Copy-Item -Force (Join-Path $here 'config.yaml.template') $deployDir
$serviceScript = Join-Path $deployDir 'hermes_service.py'

$common = @{
    hermes_home = $HermesHome
    source_dir  = $source
    python      = $venvPython
}
if ($nodeDir) { $common.node_dir = $nodeDir }

$roles = @(
    @{
        role      = 'gateway'
        service   = 'HermesGateway'
        arguments = @('gateway', 'run')
        # Drains in-flight work and releases its locks; the service wrapper
        # kills the process tree only if this does not finish in time.
        stop      = @('gateway', 'stop')
    },
    @{
        role      = 'dashboard'
        service   = 'HermesDashboard'
        # --skip-build: serving normally rebuilds the web bundle with npm
        # first. The bundle is already built, in the release, and there is no
        # registry here to build against. --no-open: there is no desktop to
        # open a browser on.
        arguments = @('dashboard', '--host', $DashboardHost, '--port', "$DashboardPort", '--skip-build', '--no-open')
        stop      = @('dashboard', '--stop')
    }
)

foreach ($entry in $roles) {
    $settings = $common.Clone()
    $settings.arguments = $entry.arguments
    $settings.stop_arguments = $entry.stop
    $settings | ConvertTo-Json | Set-Content (Join-Path $deployDir "service-$($entry.role).json") -Encoding UTF8

    $existing = Get-Service -Name $entry.service -ErrorAction SilentlyContinue
    if ($existing) {
        Note "$($entry.service) exists; stopping it to update"
        if ($existing.Status -ne 'Stopped') { Stop-Service $entry.service -Force; Start-Sleep -Seconds 3 }
        & $venvPython $serviceScript $entry.role remove | Out-Null
        Start-Sleep -Seconds 2
    }
    Invoke-Native $venvPython @($serviceScript, $entry.role, '--startup', 'auto', 'install') `
        "Registering $($entry.service) failed."
    if ($ServiceAccount) {
        Note "$($entry.service) will run as $ServiceAccount -- set its password with services.msc (see DEPLOY-HERMES.md)"
        & sc.exe config $entry.service obj= $ServiceAccount | Out-Null
    }
    # Restart on failure rather than staying down until someone notices. This
    # is also what covers a service that started before a network vault path
    # was available at boot.
    & sc.exe failure $entry.service reset= 86400 actions= restart/5000/restart/20000/restart/60000 | Out-Null
    Good "$($entry.service) registered"
}

# --------------------------------------------------------------------------
Step 'Pointing Second Brain at this Hermes'
# Only the two lines that say where Hermes is. Everything else Hermes needs
# from Second Brain -- the vault path, the data root, the shared Skill
# managers on PYTHONPATH -- Second Brain writes itself when those two are
# saved, and it is the only thing that knows how (business/setup_wizard.py).
# Reimplementing that here is how the two would drift.
# --------------------------------------------------------------------------
$secondBrainEnv = Join-Path $SecondBrainBackend '.env'
if (Test-Path $secondBrainEnv) {
    $lines = Get-Content $secondBrainEnv
    $updated = @()
    $filled = @()
    foreach ($line in $lines) {
        if ($line -match '^\s*HERMES_BASE_URL\s*=\s*$') {
            $updated += "HERMES_BASE_URL=http://${DashboardHost}:${DashboardPort}"
            $filled += 'HERMES_BASE_URL'
        } elseif ($line -match '^\s*HERMES_HOME_PATH\s*=\s*$') {
            $updated += "HERMES_HOME_PATH=$HermesHome"
            $filled += 'HERMES_HOME_PATH'
        } else {
            $updated += $line
        }
    }
    if ($filled) {
        Set-Content -Path $secondBrainEnv -Value $updated -Encoding UTF8
        Good "filled $($filled -join ' and ') in $secondBrainEnv"
        Note 'restart the SecondBrain service for it to read them'
    } else {
        Note "$secondBrainEnv already has its Hermes settings; left alone"
    }
} else {
    Note "no Second Brain install at $SecondBrainBackend; nothing to point at this Hermes"
    Note "when there is one, set HERMES_BASE_URL=http://${DashboardHost}:${DashboardPort} and HERMES_HOME_PATH=$HermesHome in its .env"
}

Write-Host "`nInstalled." -ForegroundColor Green
Write-Host "Next: put the inference key in $envFile, check the model lines in $configFile," -ForegroundColor Green
Write-Host "then 'Start-Service HermesGateway; Start-Service HermesDashboard'." -ForegroundColor Green
Write-Host "Then run .\verify-hermes.ps1 -DashboardPort $DashboardPort to check it is really serving." -ForegroundColor Green
