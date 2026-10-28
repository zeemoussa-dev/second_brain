<#
.SYNOPSIS
  Installs Second Brain on an offline Windows Server from this release folder.

.DESCRIPTION
  Run from an ELEVATED PowerShell, on the server, with the release folder
  already copied there. It reaches no network: every package it installs comes
  from .\vendor.

  It is safe to run again. Each step checks whether it is already done, so a
  run that failed halfway can simply be repeated.

.PARAMETER InstallRoot
  Where the application lives. Default C:\SecondBrain.

.PARAMETER DataRoot
  Where this install keeps its own state -- accounts, chats, the note index,
  installed plugins. Must NOT be inside the vault.

.PARAMETER VaultPath
  The Obsidian vault this install reads.

.PARAMETER Port
  The port to serve on. 443 with a certificate, 80 without.

.PARAMETER CertificateFile
.PARAMETER CertificateKeyFile
  PEM certificate and private key. Supplied by the company; see DEPLOY.md.
  Omit both to run without TLS (then use -Port 80).

.EXAMPLE
  .\install.ps1 -VaultPath D:\Vault -DataRoot D:\SecondBrainData `
                -CertificateFile C:\certs\sb.crt -CertificateKeyFile C:\certs\sb.key
#>
[CmdletBinding()]
param(
    [string]$InstallRoot = 'C:\SecondBrain',
    [Parameter(Mandatory = $true)][string]$DataRoot,
    [Parameter(Mandatory = $true)][string]$VaultPath,
    [int]$Port = 443,
    [string]$CertificateFile,
    [string]$CertificateKeyFile,
    [string]$ServiceAccount
)

$ErrorActionPreference = 'Stop'
$release = $PSScriptRoot
$pythonVersionWanted = '3.11'

function Step([string]$text) { Write-Host "`n=== $text" -ForegroundColor Cyan }
function Note([string]$text) { Write-Host "    $text" -ForegroundColor DarkGray }
function Good([string]$text) { Write-Host "    $text" -ForegroundColor Green }

# --------------------------------------------------------------------------
Step 'Checking this can work at all'
# Every one of these is cheaper to find now than after a half-install.
# --------------------------------------------------------------------------
$elevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
            ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $elevated) { throw 'Run this from an elevated PowerShell: it installs a service and binds a privileged port.' }

if (-not (Test-Path $VaultPath)) { throw "No vault at $VaultPath. Create or mount it first." }
if ($DataRoot -like "$VaultPath*") {
    throw "DataRoot is inside the vault. Keep them apart: the app's own state in the vault is what broke every Skill on 2026-09-03."
}
if ($CertificateFile -xor $CertificateKeyFile) {
    throw 'Give both -CertificateFile and -CertificateKeyFile, or neither.'
}
if ($CertificateFile) {
    foreach ($file in $CertificateFile, $CertificateKeyFile) {
        if (-not (Test-Path $file)) { throw "No such certificate file: $file" }
    }
} elseif ($Port -eq 443) {
    throw 'Port 443 with no certificate. Pass -CertificateFile and -CertificateKeyFile, or use -Port 80.'
}

# Something else on the port is the most common cause of a service that
# installs cleanly and then will not start.
$holder = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($holder) {
    $owner = (Get-Process -Id $holder.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    throw "Port $Port is already held by $owner (pid $($holder.OwningProcess)). On a fresh Windows Server this is usually IIS or WinRM; stop it or choose another port."
}
Good 'elevated, vault present, data root separate, port free'

# --------------------------------------------------------------------------
Step "Python $pythonVersionWanted"
# --------------------------------------------------------------------------
$python = Get-Command python -ErrorAction SilentlyContinue
$haveRightPython = $false
if ($python) {
    $reported = (& $python.Source --version 2>&1) -replace 'Python\s+', ''
    $haveRightPython = $reported.StartsWith($pythonVersionWanted)
    Note "found Python $reported"
}
if (-not $haveRightPython) {
    $installer = Get-ChildItem (Join-Path $release 'vendor\python') -Filter '*.exe' | Select-Object -First 1
    Note "installing $($installer.Name) for all users"
    # InstallAllUsers: a service account has no profile of its own, so a
    # per-user Python would be invisible to it.
    $arguments = '/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_pip=1', 'Include_test=0'
    $result = Start-Process -FilePath $installer.FullName -ArgumentList $arguments -Wait -PassThru
    if ($result.ExitCode -ne 0) { throw "The Python installer exited with $($result.ExitCode)." }
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Python installed but is not on PATH. Open a new elevated shell and run this again.' }
}
Good "python: $(& python --version)"

# --------------------------------------------------------------------------
Step 'Copying the application'
# --------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $release 'app\*') $InstallRoot
Good "application at $InstallRoot"

# --------------------------------------------------------------------------
Step 'Creating the virtual environment from the vendored wheels'
# A venv is built HERE rather than copied: one built on the release machine
# hard-codes that machine's user path and would not run under this account.
# --------------------------------------------------------------------------
$venv = Join-Path $InstallRoot 'src\backend\.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    & python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }
}
$wheels = Join-Path $release 'vendor\wheels'
# --no-index: never reach for a package index. On this machine there is none,
# and a silent attempt would hang for its timeout instead of failing.
& $venvPython -m pip install --no-index --find-links $wheels --upgrade pip setuptools wheel 2>&1 | Select-Object -Last 2
& $venvPython -m pip install --no-index --find-links $wheels -r (Join-Path $InstallRoot 'src\backend\requirements.txt') 2>&1 | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) { throw 'Installing the backend packages failed. The wheels may be built for a different Python minor version than the one installed here.' }
Good 'backend packages installed'

# --------------------------------------------------------------------------
Step 'Unpacking the Node toolchain'
# Only needed when installing or updating a plugin, which rebuilds the UI on
# this machine -- but it cannot be fetched later, so it travels now.
# --------------------------------------------------------------------------
$toolsNode = Join-Path $InstallRoot 'tools\node'
if (-not (Test-Path (Join-Path $toolsNode 'node.exe'))) {
    New-Item -ItemType Directory -Force -Path (Split-Path $toolsNode) | Out-Null
    Copy-Item -Recurse -Force (Join-Path $release 'vendor\node') $toolsNode
}
$modules = Join-Path $InstallRoot 'src\frontend\node_modules'
if (-not (Test-Path $modules)) {
    Note 'expanding node_modules (a few minutes)'
    Expand-Archive -Path (Join-Path $release 'vendor\node_modules.zip') -DestinationPath (Join-Path $InstallRoot 'src\frontend') -Force
}
Good 'node toolchain in place'

# --------------------------------------------------------------------------
Step 'Writing this install''s settings'
# The wizard can do this in the browser, but a server install should come up
# configured rather than asking someone to fill a form on a machine they may
# only reach through a jump host.
# --------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
$envFile = Join-Path $InstallRoot 'src\backend\.env'
if (Test-Path $envFile) {
    Note '.env already exists; leaving it alone'
} else {
    @(
        "VAULT_PATH=$VaultPath",
        "SECOND_BRAIN_DATA_PATH=$DataRoot",
        '# Filled in from the browser at Settings > System, or here before first start.',
        'SELF_EMAIL=',
        'COMPASS_BASE_URL=',
        'COMPASS_API_KEY=',
        'COMPASS_MODEL=',
        '# Hermes is optional. Leave blank on an install that has no agent runtime.',
        'HERMES_BASE_URL=',
        'HERMES_HOME_PATH=',
        '# One origin in production, so there is no cross-origin caller to allow.',
        'CORS_ALLOWED_ORIGINS='
    ) | Set-Content $envFile -Encoding UTF8
    Good "wrote $envFile"
}

# --------------------------------------------------------------------------
Step 'Registering the Windows service'
# --------------------------------------------------------------------------
$serviceConfig = @{
    backend_dir = (Join-Path $InstallRoot 'src\backend')
    host        = '0.0.0.0'
    port        = $Port
}
if ($CertificateFile) {
    $serviceConfig.ssl_certfile = $CertificateFile
    $serviceConfig.ssl_keyfile = $CertificateKeyFile
}
$serviceConfig | ConvertTo-Json | Set-Content (Join-Path $InstallRoot 'deploy\service.json') -Encoding UTF8

$existing = Get-Service -Name 'SecondBrain' -ErrorAction SilentlyContinue
if ($existing) {
    Note 'service exists; stopping it to update'
    if ($existing.Status -ne 'Stopped') { Stop-Service 'SecondBrain' -Force; Start-Sleep -Seconds 3 }
    & $venvPython (Join-Path $InstallRoot 'deploy\service.py') remove | Out-Null
    Start-Sleep -Seconds 2
}
& $venvPython (Join-Path $InstallRoot 'deploy\service.py') --startup auto install
if ($LASTEXITCODE -ne 0) { throw 'Registering the service failed.' }

if ($ServiceAccount) {
    Note "the service will run as $ServiceAccount -- set its password with services.msc (see DEPLOY.md)"
    & sc.exe config SecondBrain obj= $ServiceAccount | Out-Null
}
# Restart on failure rather than staying down until someone notices.
& sc.exe failure SecondBrain reset= 86400 actions= restart/5000/restart/20000/restart/60000 | Out-Null
Good 'service registered, set to start at boot, restarts on failure'

Write-Host "`nInstalled." -ForegroundColor Green
Write-Host "Next: fill in COMPASS_* in $envFile, then 'Start-Service SecondBrain'." -ForegroundColor Green
Write-Host "Then run .\verify.ps1 -Port $Port to check it is really serving." -ForegroundColor Green
