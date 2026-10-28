<#
.SYNOPSIS
  Assembles the offline release for Hermes, the agent runtime. RUN THIS HERE,
  on a machine with internet and a working Hermes install. The server never
  needs any.

.DESCRIPTION
  Hermes is a separate product -- NousResearch/hermes-agent, MIT licensed --
  that Second Brain uses as its execution layer: it runs the scheduled jobs
  and the capture, and it answers the REST calls Second Brain makes. It has
  its own release because it has its own lifecycle: a Second Brain server
  without it is a complete install (every screen says "not configured"
  rather than looking broken).

  Upstream's own installer cannot be used on an air-gapped server. It clones
  from GitHub, resolves packages from PyPI, downloads a Node toolchain and a
  browser, and has no offline mode -- so this builds the same end state from
  files instead, and `install-hermes.ps1` lays it down.

  What this release deliberately does NOT contain:

    * Any of this machine's Hermes state. No profiles, no sessions, no
      auth.json, no config.yaml, no .env, no logs, no caches, no skills
      written here. The server is a clean install under a different account
      (operator, 2026-10-28: "it will be running under a Different
      Username").
    * `node_modules`. 366 MB whose only job is building the dashboard's web
      bundle -- which is built HERE and shipped as 3 MB of output instead.
    * Any virtual environment. One built here hard-codes this machine's user
      path; the installer builds a fresh one from the vendored wheels.

.PARAMETER HermesSource
  The Hermes checkout to build from. Defaults to this machine's install.

.PARAMETER Destination
  Where to write the release. Defaults to .\Release-Hermes beside the repo.
#>
[CmdletBinding()]
param(
    # Computed below, not here: `$PSScriptRoot` is not reliably populated
    # inside a param() default under Windows PowerShell 5.1.
    [string]$HermesSource,
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }
$repo = Split-Path (Split-Path $here -Parent) -Parent
if (-not $HermesSource) { $HermesSource = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent' }
if (-not $Destination) { $Destination = Join-Path $repo 'Release-Hermes' }

# Hermes' interpreter is not installed, it is COPIED -- see 'Vendoring the
# Python runtime' below for why python.org's installer is the wrong choice
# for this product specifically.
$runtimeDirectoryName = 'cpython-3.11-windows-x86_64-none'

function Step([string]$text) { Write-Host "`n=== $text" -ForegroundColor Cyan }
function Note([string]$text) { Write-Host "    $text" -ForegroundColor DarkGray }

function Invoke-Native {
    <#
      Runs an external program and fails on its EXIT CODE, not on whether it
      wrote to stderr. Under Windows PowerShell 5.1 with
      $ErrorActionPreference = 'Stop', any line a native program writes to
      stderr becomes a terminating error -- so pip printing an ordinary
      progress line killed this build while the command had succeeded.
    #>
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

function Normalize-PackageName([string]$name) {
    # PEP 503: `ruamel.yaml`, `ruamel-yaml` and `Ruamel_Yaml` are one package.
    # The two sources merged below spell them differently.
    ($name -replace '[-_.]+', '-').ToLowerInvariant()
}

# --------------------------------------------------------------------------
Step 'Checking the source install'
# --------------------------------------------------------------------------
if (-not (Test-Path (Join-Path $HermesSource 'pyproject.toml'))) {
    throw "No Hermes checkout at $HermesSource. Pass -HermesSource."
}
$hermesVenvPython = Join-Path $HermesSource 'venv\Scripts\python.exe'
if (-not (Test-Path $hermesVenvPython)) {
    throw "No virtual environment at $HermesSource\venv. The release is built from the packages a WORKING install resolved, so there has to be one."
}
$webDist = Join-Path $HermesSource 'hermes_cli\web_dist'
if (-not (Test-Path (Join-Path $webDist 'index.html'))) {
    # Not a nicety: Second Brain reads its Hermes session token out of the
    # dashboard's own HTML (app/hermes/rest.py). No bundle, no token, no
    # integration -- and the bundle cannot be built on the server, which has
    # neither npm nor a registry.
    throw "No built dashboard bundle at $webDist. Build it here first: cd $HermesSource\web; npm run build"
}
$hermesVersion = (Select-String -Path (Join-Path $HermesSource 'pyproject.toml') -Pattern '^version\s*=\s*"([^"]+)"' |
                  Select-Object -First 1).Matches.Groups[1].Value
$hermesCommit = (& git -C $HermesSource rev-parse HEAD).Trim()
Note "hermes-agent $hermesVersion at $($hermesCommit.Substring(0,8))"
Note "python $((& $hermesVenvPython --version) -replace 'Python\s+','')"

if (Test-Path $Destination) {
    Write-Host "Removing the previous release at $Destination" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $Destination
}
$app = Join-Path $Destination 'app'
$vendor = Join-Path $Destination 'vendor'
New-Item -ItemType Directory -Force -Path $app, $vendor | Out-Null

# --------------------------------------------------------------------------
Step 'Exporting the Hermes source'
# `git archive` of the committed tree, so what ships is upstream's code and
# nothing this machine put beside it: no venv, no node_modules, no .git, no
# profiles, no runtime scratch. It also means no update check ever runs on
# the server -- Hermes counts commits behind origin/main to decide, finds no
# checkout, and silently does nothing. On a box with no internet that is the
# behaviour we want.
# --------------------------------------------------------------------------
$archive = Join-Path $env:TEMP 'hermes-source.zip'
Invoke-Native 'git' @('-C', $HermesSource, 'archive', '--format=zip', '--output', $archive, 'HEAD') `
    'git archive failed; the release would have no source.'
Expand-Archive -Path $archive -DestinationPath (Join-Path $app 'hermes-agent') -Force
Remove-Item $archive -Force
Note "source: $((Get-ChildItem -Recurse -File (Join-Path $app 'hermes-agent')).Count) files"

# The dashboard's web bundle, built from this same commit. Shipped as output
# rather than built on the server: `hermes dashboard --skip-build` exists for
# exactly this case ("non-interactive contexts where npm may not be
# available"), and it saves shipping 366 MB of node_modules to produce 3 MB.
Copy-Item -Recurse $webDist (Join-Path $app 'hermes-agent\hermes_cli\web_dist')
Note ('dashboard bundle: {0:N1} MB' -f ((Get-ChildItem -Recurse -File $webDist | Measure-Object Length -Sum).Sum / 1MB))

# Our own scripts: the installer, the service wrapper, the checker, the
# config template.
Copy-Item -Recurse $here (Join-Path $app 'deploy')
Remove-Item (Join-Path $app 'deploy\build-hermes-release.ps1') -ErrorAction SilentlyContinue

# --------------------------------------------------------------------------
Step 'Vendoring the Python runtime'
# Hermes manages its own interpreter rather than using a system one, and that
# is load-bearing here: `hermes_cli/sqlite_runtime.py` treats any SQLite
# below 3.51.3 as carrying the WAL-reset bug, and keeps every database out
# of WAL mode when it finds one. python.org's 3.11 installers ship SQLite
# 3.45 -- 3.11.9 is the last of them, security-only since April 2024, so
# there is no newer one to reach for -- which would leave the gateway
# writing session state through the coarsest locking SQLite has, forever.
# The runtime Hermes installed here is 3.11.16 with SQLite 3.53.1.
#
# It is relocatable by design, carries its own pip and ensurepip, and copying
# it means the server needs no machine-wide Python install at all for Hermes.
# --------------------------------------------------------------------------
# The versioned directory is the real one; Hermes keeps an unversioned
# junction beside it pointing here. A junction cannot be copied as a
# directory, so the real one is the source and the installer puts it back
# under the name Hermes' own tooling looks for.
$runtimeSource = Get-ChildItem (Join-Path $HermesSource '.hermes-runtime\python') -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.LinkType -ne 'Junction' -and (Test-Path (Join-Path $_.FullName 'python.exe')) } |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $runtimeSource) {
    throw "No managed Python runtime under $HermesSource\.hermes-runtime\python. This release copies Hermes' own interpreter rather than installing one; a source install that never provisioned it cannot be the build source."
}
Copy-Item -Recurse $runtimeSource.FullName (Join-Path $vendor "python-runtime\$runtimeDirectoryName")
$runtimePython = Join-Path $vendor "python-runtime\$runtimeDirectoryName\python.exe"
$runtimeFacts = & $runtimePython -c "import sys,sqlite3;print(sys.version.split()[0],sqlite3.sqlite_version)"
$pythonVersion, $sqliteVersion = $runtimeFacts.Trim() -split '\s+'
Note "python $pythonVersion, sqlite $sqliteVersion (from $($runtimeSource.Name))"
if ([version]$sqliteVersion -lt [version]'3.51.3') {
    throw "The vendored runtime's SQLite is $sqliteVersion, which Hermes treats as carrying the WAL-reset bug. Shipping it would install a Hermes that cannot use WAL mode."
}

# uv, because Hermes bootstraps it FROM THE INTERNET when it is missing
# (`managed_uv.ensure_uv`). Nothing on the serving path calls it -- setup,
# update and recovery do -- but an offline box should not have a command
# that quietly tries to download a 40 MB binary.
$uvExecutable = Join-Path (Split-Path $HermesSource -Parent) 'bin\uv.exe'
if (Test-Path $uvExecutable) {
    New-Item -ItemType Directory -Force -Path (Join-Path $vendor 'bin') | Out-Null
    Copy-Item $uvExecutable (Join-Path $vendor 'bin\uv.exe')
    Note "uv $((& $uvExecutable --version) -replace 'uv\s+','' -replace '\s.*','')"
} else {
    Note 'no uv.exe beside the source; Hermes will try to download one if a setup or update path ever runs'
}

# --------------------------------------------------------------------------
Step 'Resolving what Hermes needs'
# Two sources, deliberately merged:
#
#   * `uv export` of uv.lock -- upstream's own exact-pinned resolution. 68
#     packages, every direct dependency pinned to ==X.Y.Z.
#   * what the working install ACTUALLY has installed. Hermes lazy-installs
#     provider and channel extras the first time a backend is picked
#     (tools/lazy_deps.py), so a real install carries ~46 packages the lock
#     does not list -- `mcp` among them, which is how Second Brain's own
#     tools reach Hermes.
#
# On a server with no network a package that is not in the release can never
# be installed, so the union of the two travels rather than the smaller set.
# --------------------------------------------------------------------------
$requirements = Join-Path $vendor 'requirements-hermes.txt'
$locked = Join-Path $env:TEMP 'hermes-locked.txt'
$uv = Join-Path (Split-Path $HermesSource -Parent) 'bin\uv.exe'
if (-not (Test-Path $uv)) { $uv = 'uv' }
Push-Location $HermesSource
try {
    Invoke-Native $uv @('export', '--no-dev', '--no-hashes', '--no-emit-project',
                        '--no-annotate', '--no-header', '--quiet', '-o', $locked) `
        'uv export failed; the locked package set could not be read.'
} finally { Pop-Location }

$lines = @()
$seen = @{}
foreach ($line in Get-Content $locked) {
    $text = $line.Trim()
    if (-not $text -or $text.StartsWith('#')) { continue }
    $name = Normalize-PackageName (($text -split '==')[0]).Trim()
    $seen[$name] = $true
    # Markers travel as written: pip evaluates them, so the posix-only
    # entries (ptyprocess, uvloop) resolve to nothing on Windows by
    # themselves rather than by us second-guessing the lock.
    $lines += $text
}
$lockedCount = $lines.Count

$ErrorActionPreference = 'Continue'
$frozen = & $hermesVenvPython -m pip freeze 2> $null
$ErrorActionPreference = 'Stop'
$extras = 0
foreach ($line in $frozen) {
    $text = $line.Trim()
    if (-not $text -or $text.StartsWith('#') -or $text.StartsWith('-e ') -or $text -notmatch '==') { continue }
    $name = Normalize-PackageName (($text -split '==')[0]).Trim()
    # The project itself is installed into the venv as an editable; it is the
    # source tree, not a package to download.
    if ($name -eq 'hermes-agent') { continue }
    if ($seen.ContainsKey($name)) { continue }
    $seen[$name] = $true
    $lines += $text
    $extras++
}
Set-Content -Path $requirements -Value $lines -Encoding ASCII
Note "$lockedCount from uv.lock, $extras more the live install resolved"

# --------------------------------------------------------------------------
Step 'Vendoring the packages as wheels'
# --------------------------------------------------------------------------
$wheels = Join-Path $vendor 'wheels'
New-Item -ItemType Directory -Force -Path $wheels | Out-Null

# This network intercepts TLS, and Python ships its own CA bundle that knows
# nothing about the corporate root -- so pip refuses every download with
# CERTIFICATE_VERIFY_FAILED while a browser on the same machine is fine.
# Exporting what Windows already trusts sidesteps that and keeps verification
# ON; `--trusted-host` would turn it off, and this is the machine that
# decides what ends up inside the release. A build-machine concern only: the
# server has no network to verify against.
$trustBundle = Join-Path $env:TEMP 'windows-trust-bundle.pem'
$pem = New-Object System.Text.StringBuilder
foreach ($store in 'Root', 'CA') {
    foreach ($certificate in Get-ChildItem "Cert:\LocalMachine\$store") {
        [void]$pem.AppendLine('-----BEGIN CERTIFICATE-----')
        [void]$pem.AppendLine([Convert]::ToBase64String($certificate.RawData, 'InsertLineBreaks'))
        [void]$pem.AppendLine('-----END CERTIFICATE-----')
    }
}
Set-Content -Path $trustBundle -Value $pem.ToString() -Encoding ASCII
Note "trusting what Windows trusts ($((Get-ChildItem 'Cert:\LocalMachine\Root').Count) roots)"

# --only-binary: a package with no wheel for this platform would arrive as an
# sdist the SERVER would have to compile, with no compiler and no network.
# Far better to fail here, where it can be solved.
Invoke-Native $hermesVenvPython @(
    '-m', 'pip', 'download', '--cert', $trustBundle, '--quiet',
    '-r', $requirements, '-d', $wheels, '--only-binary=:all:'
) 'pip download failed. A package may have no wheel for this platform; resolve it here, not on the server.'

# setuptools and wheel are not optional extras here: the installer installs
# Hermes itself with --no-build-isolation, which means the build backend has
# to be IN the venv rather than fetched into a sandbox. pyproject pins the
# version it wants.
$buildBackend = (Select-String -Path (Join-Path $HermesSource 'pyproject.toml') -Pattern 'setuptools==([0-9.]+)' |
                 Select-Object -First 1).Matches.Groups[1].Value
Invoke-Native $hermesVenvPython @(
    '-m', 'pip', 'download', '--cert', $trustBundle, '--quiet',
    'pip', "setuptools==$buildBackend", 'wheel', '-d', $wheels
) 'Could not vendor the build backend.'
Note "$((Get-ChildItem $wheels -File).Count) files, $('{0:N0} MB' -f ((Get-ChildItem $wheels -File | Measure-Object Length -Sum).Sum / 1MB))"

# --------------------------------------------------------------------------
Step 'Vendoring the Node toolchain'
# Hermes shells out to node and npm for a few channels and tools. None of it
# is needed to serve, but none of it can be fetched later either, so the
# toolchain travels and the skills that need it work.
# --------------------------------------------------------------------------
$nodeSource = Join-Path (Split-Path $HermesSource -Parent) 'node'
if (Test-Path (Join-Path $nodeSource 'node.exe')) {
    Copy-Item -Recurse $nodeSource (Join-Path $vendor 'node')
    $nodeVersion = (& (Join-Path $nodeSource 'node.exe') --version).Trim()
    Note "node $nodeVersion"
} else {
    $nodeVersion = $null
    Note 'no node toolchain beside the source; skipping (channels needing node will not work)'
}

# --------------------------------------------------------------------------
Step 'Writing the version stamp'
# --------------------------------------------------------------------------
@{
    product        = 'hermes-agent'
    built_at       = (Get-Date).ToString('o')
    hermes_version = $hermesVersion
    hermes_commit  = $hermesCommit
    upstream       = 'https://github.com/NousResearch/hermes-agent (MIT)'
    python_version = $pythonVersion
    sqlite_version = $sqliteVersion
    node_version   = $nodeVersion
    packages       = (Get-ChildItem $wheels -File).Count
    built_for      = 'Second Brain ' + (& git -C $repo rev-parse --short HEAD).Trim()
    built_on       = [System.Environment]::OSVersion.VersionString
} | ConvertTo-Json | Set-Content (Join-Path $Destination 'RELEASE.json') -Encoding UTF8

Copy-Item (Join-Path $here 'DEPLOY-HERMES.md') $Destination -ErrorAction SilentlyContinue

# --------------------------------------------------------------------------
Step 'Checking nothing private travelled'
# This machine's Hermes home sits one directory above the source and holds
# profiles, sessions, auth.json and a live API key. A release is copied to a
# server by someone who will not read every file, so the check belongs here
# rather than in a reviewer's head.
# --------------------------------------------------------------------------
$forbidden = @()
# Secrets, by exact name, anywhere in the release. `.env.example` is
# upstream's own 535-line template and is meant to travel; a real `.env` is
# not, and both end in the same four characters -- hence the exact names.
# `vendor\` is third-party distributions whose own trees legitimately carry
# test certificates, so they are not scanned for those.
$forbidden += Get-ChildItem -Recurse -Force -File $app -Include 'auth.json', 'config.yaml', '.env' -ErrorAction SilentlyContinue
$forbidden += Get-ChildItem -Recurse -Force -File $app -Include '*.pem', '*.pfx', '*.key' -ErrorAction SilentlyContinue
$forbidden += Get-ChildItem -Recurse -Force -Directory $app -Include '.venv', 'venv', '.git', 'node_modules' -ErrorAction SilentlyContinue

# This machine's Hermes HOME sits one directory above the source and holds
# the profiles, the sessions, the caches and the logs. Those are checked for
# where a home would have been copied to -- beside the source, or in place of
# it -- and NOT by name anywhere in the tree: upstream's own desktop app has
# source directories called `profiles` and `sessions`, and a check that
# cannot tell those apart from a leak is a check that gets switched off.
foreach ($relative in 'profiles', 'sessions', 'hermes-agent\profiles',
                      'hermes-agent\sessions', 'hermes-agent\logs', 'hermes-agent\cache') {
    $candidate = Join-Path $app $relative
    if (Test-Path $candidate) { $forbidden += Get-Item $candidate }
}
if ($forbidden) {
    $forbidden | ForEach-Object { Write-Host "    LEAK: $($_.FullName)" -ForegroundColor Red }
    throw 'The release contains files it must not ship. Nothing was published.'
}
Note 'no profiles, no sessions, no keys, no config, no venv'

$size = (Get-ChildItem -Recurse -File $Destination | Measure-Object Length -Sum).Sum / 1GB
Write-Host "`nRelease ready: $Destination" -ForegroundColor Green
Write-Host ('{0:N2} GB, hermes-agent {1} at {2}' -f $size, $hermesVersion, $hermesCommit.Substring(0, 8)) -ForegroundColor Green
Write-Host 'Copy the whole folder to the server and read DEPLOY-HERMES.md.' -ForegroundColor Green
