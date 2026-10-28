<#
.SYNOPSIS
  Assembles the offline release for a production server. RUN THIS HERE, on a
  machine with internet. The server never needs any.

.DESCRIPTION
  Produces a single folder containing the application's code, every package it
  needs as a file, the toolchains to install them, and the scripts that do the
  installing. Nothing in it is downloaded at install time.

  What it deliberately does NOT contain:

    * Any of this machine's data. No vault, no .env, no config folder, no
      chats, no auth database, no certificates, no Hermes profiles and no
      Hermes auth.json. The server is a clean install under a different
      account (operator, 2026-10-28: "it will be running under a Different
      Username").
    * Any of the development lifecycle. No Implementation/, no sprints or
      user stories, no Documentation/, no html-prototype/, no .claude/, no
      BACKLOG/BUGS/MEMORY/CHANGELOG, no .git, no tests (operator: "I want
      only the code in The Package Not my Whole Dev Life Cycle").
    * Any virtual environment. `.venv` here hard-codes this machine's user
      path and cannot be copied to a server with a different account; the
      installer builds a fresh one from the vendored wheels.

.PARAMETER Destination
  Where to write the release. Defaults to .\Release beside the repo.
#>
[CmdletBinding()]
param(
    # Computed below, not here: `$PSScriptRoot` is not reliably populated
    # inside a param() default under Windows PowerShell 5.1.
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }
$repo = Split-Path $here -Parent
if (-not $Destination) { $Destination = Join-Path $repo 'Release' }

# The Python the backend is tested on, and the one the vendored wheels are
# built for. A different minor version on the server means the wheels may not
# match, which is why the installer checks rather than hoping.
$pythonVersion = '3.11.9'
$pythonInstaller = "python-$pythonVersion-amd64.exe"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonInstaller"

function Step([string]$text) { Write-Host "`n=== $text" -ForegroundColor Cyan }
function Note([string]$text) { Write-Host "    $text" -ForegroundColor DarkGray }

function Invoke-Native {
    <#
      Runs an external program and fails on its EXIT CODE, not on whether it
      wrote to stderr.

      Under Windows PowerShell 5.1 with $ErrorActionPreference = 'Stop', any
      line a native program writes to stderr becomes a terminating error --
      so pip printing an ordinary progress line, or npm printing a notice,
      killed this build while the command itself had succeeded. Twice.
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

if (Test-Path $Destination) {
    Write-Host "Removing the previous release at $Destination" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $Destination
}

$app = Join-Path $Destination 'app'
$vendor = Join-Path $Destination 'vendor'
New-Item -ItemType Directory -Force -Path $app, $vendor | Out-Null

# --------------------------------------------------------------------------
Step 'Building the web interface'
# Built HERE so the server needs no build step to come up. VITE_API_BASE_URL
# is empty on purpose: the UI and the API are one origin in production, so
# every call is relative and nothing has to know the server's hostname.
# --------------------------------------------------------------------------
Push-Location (Join-Path $repo 'src\frontend')
try {
    $env:VITE_API_BASE_URL = ''
    Invoke-Native (Join-Path $repo 'tools\node\npx.cmd') @('vite', 'build') `
        'The frontend build failed; the release would be unusable.'
} finally {
    Remove-Item Env:\VITE_API_BASE_URL -ErrorAction SilentlyContinue
    Pop-Location
}

# --------------------------------------------------------------------------
Step 'Copying the application code'
# --------------------------------------------------------------------------
$backendSource = Join-Path $repo 'src\backend'
$backendTarget = Join-Path $app 'src\backend'
New-Item -ItemType Directory -Force -Path $backendTarget | Out-Null

# The code and its manifest, and nothing else from the backend folder: no
# .venv, no .env, no __pycache__, no tests, no backend.log.
Copy-Item -Recurse (Join-Path $backendSource 'app') (Join-Path $backendTarget 'app')
Copy-Item (Join-Path $backendSource 'requirements.txt') $backendTarget
Get-ChildItem -Recurse -Force -Directory (Join-Path $backendTarget 'app') |
    Where-Object { $_.Name -eq '__pycache__' } |
    Remove-Item -Recurse -Force
Note "backend: $((Get-ChildItem -Recurse -File (Join-Path $backendTarget 'app')).Count) files"

# The frontend SOURCE travels too, not just the built output: installing a
# plugin composes its screens into the app and rebuilds it, on the server.
$frontendSource = Join-Path $repo 'src\frontend'
$frontendTarget = Join-Path $app 'src\frontend'
New-Item -ItemType Directory -Force -Path $frontendTarget | Out-Null
foreach ($item in 'src', 'public', 'dist', 'index.html', 'package.json', 'package-lock.json',
                  'tsconfig.json', 'tsconfig.app.json', 'tsconfig.node.json', 'vite.config.ts') {
    $from = Join-Path $frontendSource $item
    if (Test-Path $from) { Copy-Item -Recurse $from (Join-Path $frontendTarget $item) }
}

# The plugins, so they can be installed on a server with no Marketplace feed.
Copy-Item -Recurse (Join-Path $repo 'src\marketplace') (Join-Path $app 'src\marketplace')

# The service wrapper and the install scripts. The build-machine scripts are
# removed again: they need this repo and a network, so on the server they
# could only mislead.
Copy-Item -Recurse $here (Join-Path $app 'deploy')
foreach ($buildMachineOnly in 'build-release.ps1', 'stage-for-transfer.ps1', 'build-hermes-release.ps1') {
    Remove-Item (Join-Path $app "deploy\$buildMachineOnly") -ErrorAction SilentlyContinue
}
# Hermes is a separate product with a release of its own; its installer ships
# in that release, not in this one.
Remove-Item -Recurse (Join-Path $app 'deploy\hermes') -ErrorAction SilentlyContinue

# --------------------------------------------------------------------------
Step 'Vendoring Python'
# --------------------------------------------------------------------------
$pythonDir = Join-Path $vendor 'python'
New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null
$installerPath = Join-Path $pythonDir $pythonInstaller
Note "downloading $pythonInstaller"
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
Note ('{0:N1} MB' -f ((Get-Item $installerPath).Length / 1MB))

# --------------------------------------------------------------------------
Step 'Vendoring the backend packages as wheels'
# Built for THIS platform and this Python minor version; the installer checks
# the server matches before it tries to use them.
# --------------------------------------------------------------------------
$wheels = Join-Path $vendor 'wheels'
New-Item -ItemType Directory -Force -Path $wheels | Out-Null

# The development venv is built by `uv`, which installs no pip -- so the
# interpreter that downloads the wheels has to be found rather than assumed.
# `ensurepip` puts one into the venv itself, which keeps the wheels matched to
# the exact interpreter the app is developed and tested against.
$builderPython = Join-Path $backendSource '.venv\Scripts\python.exe'

# Asking "is pip here?" without the question itself being fatal. Under
# Windows PowerShell 5.1 `2>&1` on a native command wraps each stderr line in
# an ErrorRecord, which with $ErrorActionPreference = 'Stop' terminates the
# script -- so a missing pip killed the build instead of being handled.
$ErrorActionPreference = 'Continue'
& $builderPython -m pip --version > $null 2> $null
$hasPip = ($LASTEXITCODE -eq 0)
if (-not $hasPip) {
    Note 'the venv has no pip (uv creates none); bootstrapping one with ensurepip'
    & $builderPython -m ensurepip --default-pip > $null 2> $null
    & $builderPython -m pip --version > $null 2> $null
    $hasPip = ($LASTEXITCODE -eq 0)
}
$ErrorActionPreference = 'Stop'
if (-not $hasPip) { throw 'No pip available to download the wheels with.' }

# This network intercepts TLS, and Python ships its own CA bundle that knows
# nothing about the corporate root -- so pip refuses every download with
# CERTIFICATE_VERIFY_FAILED while a browser on the same machine is fine
# (Deployment.md, "TLS interception"). The documented fix is the
# `pip_system_certs` package, which cannot be installed without the network it
# is needed for.
#
# Exporting what Windows already trusts sidesteps that, and keeps verification
# ON -- `--trusted-host` would turn it off, and this is the machine that
# decides what ends up inside the release.
#
# A build-machine concern only: the server has no network to verify against.
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
# sdist that the SERVER would have to compile, with no compiler and no
# network. Far better to fail here, where it can be solved.
Invoke-Native $builderPython @(
    '-m', 'pip', 'download', '--cert', $trustBundle, '--quiet',
    '-r', (Join-Path $backendSource 'requirements.txt'),
    '-d', $wheels, '--only-binary=:all:'
) 'pip download failed. A package may have no wheel for this platform; resolve it here, not on the server.'

# pip itself, so the installer can bootstrap into an offline venv.
Invoke-Native $builderPython @(
    '-m', 'pip', 'download', '--cert', $trustBundle, '--quiet',
    'pip', 'setuptools', 'wheel', '-d', $wheels
) 'Could not vendor pip itself.'
Note "$((Get-ChildItem $wheels -File).Count) packages, $('{0:N0} MB' -f ((Get-ChildItem $wheels -File | Measure-Object Length -Sum).Sum / 1MB))"

# --------------------------------------------------------------------------
Step 'Vendoring the Node toolchain and the frontend packages'
# Needed on the server because installing a plugin rebuilds the UI there.
# --------------------------------------------------------------------------
Copy-Item -Recurse (Join-Path $repo 'tools\node') (Join-Path $vendor 'node')
Note 'node: copied'

# node_modules as a folder, not an npm cache: `npm ci --offline` still
# resolves the registry for metadata on some packages, and the server has no
# registry to resolve against. A directory copy has no such failure mode.
$modulesArchive = Join-Path $vendor 'node_modules.zip'
Note 'compressing node_modules (this takes a minute)'
Compress-Archive -Path (Join-Path $frontendSource 'node_modules') -DestinationPath $modulesArchive -CompressionLevel Optimal
Note ('{0:N0} MB' -f ((Get-Item $modulesArchive).Length / 1MB))

# --------------------------------------------------------------------------
Step 'Writing the version stamp'
# --------------------------------------------------------------------------
$commit = (& git -C $repo rev-parse HEAD).Trim()
@{
    built_at       = (Get-Date).ToString('o')
    built_from     = $commit
    python_version = $pythonVersion
    node_version   = (& (Join-Path $repo 'tools\node\node.exe') --version).Trim()
    built_on       = [System.Environment]::OSVersion.VersionString
} | ConvertTo-Json | Set-Content (Join-Path $Destination 'RELEASE.json') -Encoding UTF8

Copy-Item (Join-Path $here 'DEPLOY.md') $Destination -ErrorAction SilentlyContinue

# --------------------------------------------------------------------------
Step 'Checking nothing private travelled'
# A release is copied to a server by someone who will not read every file, so
# the check belongs here rather than in a reviewer's head.
# --------------------------------------------------------------------------
# Scoped to `app\` -- OUR code, where a secret of this machine's could
# plausibly be copied by mistake. `vendor\` is third-party distributions whose
# own trees legitimately contain `node_modules` (npm's internals) and test
# certificates; scanning those produced nothing but false alarms.
$forbidden = @()
$forbidden += Get-ChildItem -Recurse -Force -File $app -Include '.env', '.env.*', 'auth.json', '*.pem', '*.pfx', '*.key' -ErrorAction SilentlyContinue
$forbidden += Get-ChildItem -Recurse -Force -Directory $app -Include '.venv', '.git', 'node_modules', '__pycache__' -ErrorAction SilentlyContinue
# An `.env` anywhere in the release is worth stopping for, wherever it came from.
$forbidden += Get-ChildItem -Recurse -Force -File $Destination -Filter '.env' -ErrorAction SilentlyContinue
if ($forbidden) {
    $forbidden | ForEach-Object { Write-Host "    LEAK: $($_.FullName)" -ForegroundColor Red }
    throw 'The release contains files it must not ship. Nothing was published.'
}

$size = (Get-ChildItem -Recurse -File $Destination | Measure-Object Length -Sum).Sum / 1GB
Write-Host "`nRelease ready: $Destination" -ForegroundColor Green
Write-Host ('{0:N2} GB, built from {1}' -f $size, $commit.Substring(0, 8)) -ForegroundColor Green
Write-Host 'Copy the whole folder to the server and read DEPLOY.md.' -ForegroundColor Green
