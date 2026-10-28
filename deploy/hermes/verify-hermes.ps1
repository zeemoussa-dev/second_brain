<#
.SYNOPSIS
  Checks that an installed Hermes is really running, from the server.

.DESCRIPTION
  Tests are not shipped in the release -- the package carries the code, not
  the development lifecycle -- so this is how an installed Hermes is checked.
  It makes the same requests Second Brain makes, in the same order, rather
  than asserting that the install script finished.

  Safe to run at any time, apart from the last check, which restarts both
  services on purpose.
#>
[CmdletBinding()]
param(
    [int]$DashboardPort = 9119,
    [string]$DashboardHost = '127.0.0.1',
    [string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { 'C:\Hermes' }),
    # The restart check costs a minute and interrupts anything running. On by
    # default the first time; worth turning off when re-checking a box that
    # is already serving people.
    [switch]$SkipRestartCheck,
    # Checks the COPIED FILES against the manifest stage-for-transfer.ps1
    # wrote, then stops. Run this before installing anything: a transfer that
    # truncated a file does not announce it, and the install built on it
    # fails much later and somewhere else.
    [switch]$Manifest
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }

if ($Manifest) {
    # Found by looking for the manifest rather than by counting directories
    # up from here, so this keeps working wherever in the release the script
    # is run from.
    $releaseRoot = $here
    while ($releaseRoot -and -not (Test-Path (Join-Path $releaseRoot 'TRANSFER.sha256'))) {
        $parent = Split-Path $releaseRoot -Parent
        if ($parent -eq $releaseRoot) { break }
        $releaseRoot = $parent
    }
    $manifestPath = Join-Path $releaseRoot 'TRANSFER.sha256'
    if (-not (Test-Path $manifestPath)) {
        throw "No TRANSFER.sha256 above $here. The build machine writes it with stage-for-transfer.ps1 -ReleasePath .\Release-Hermes; without it there is nothing to check the copy against."
    }
    Write-Host "`nChecking the copy at $releaseRoot" -ForegroundColor Cyan
    $expected = @(Get-Content -LiteralPath $manifestPath | Where-Object { $_ })
    $damaged = @()
    $checked = 0
    foreach ($line in $expected) {
        $hash, $relative = $line -split ' \*', 2
        $file = Join-Path $releaseRoot $relative
        if (-not (Test-Path -LiteralPath $file)) { $damaged += "MISSING  $relative"; continue }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash -ne $hash) { $damaged += "CORRUPT  $relative" }
        $checked++
        if ($checked % 500 -eq 0) {
            Write-Progress -Activity 'Verifying the copy' -Status "$checked of $($expected.Count)" -PercentComplete ($checked * 100 / $expected.Count)
        }
    }
    Write-Progress -Activity 'Verifying the copy' -Completed
    if ($damaged) {
        $damaged | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host "`n$($damaged.Count) file(s) did not survive the copy. Run the robocopy again -- with /Z it resumes -- then check again." -ForegroundColor Red
        exit 1
    }
    Write-Host "  ok   all $checked files match the manifest" -ForegroundColor Green
    Write-Host 'The copy is intact. Install from here.' -ForegroundColor Green
    exit 0
}
$base = "http://${DashboardHost}:${DashboardPort}"
$failures = 0
$script:sessionToken = $null

function Check([string]$what, [scriptblock]$test) {
    try {
        $detail = & $test
        Write-Host ("  ok   {0}{1}" -f $what.PadRight(44), $detail) -ForegroundColor Green
    } catch {
        $script:failures++
        Write-Host ("  FAIL {0}{1}" -f $what.PadRight(44), $_.Exception.Message) -ForegroundColor Red
    }
}

$web = @{ UseBasicParsing = $true; TimeoutSec = 30 }

Write-Host "`nChecking Hermes at $base" -ForegroundColor Cyan

Check 'the HermesGateway service is running' {
    $service = Get-Service -Name 'HermesGateway' -ErrorAction Stop
    if ($service.Status -ne 'Running') { throw "service is $($service.Status)" }
    "starts $((Get-CimInstance Win32_Service -Filter "Name='HermesGateway'").StartMode)"
}

Check 'the HermesDashboard service is running' {
    $service = Get-Service -Name 'HermesDashboard' -ErrorAction Stop
    if ($service.Status -ne 'Running') { throw "service is $($service.Status)" }
    "starts $((Get-CimInstance Win32_Service -Filter "Name='HermesDashboard'").StartMode)"
}

Check 'the inference key is set' {
    # Not whether it WORKS -- that would spend a request and need the
    # network. Whether it is there at all, which is the mistake that gets
    # made: every agent turn fails with an authentication error and the
    # screens show nothing useful about why.
    $envFile = Join-Path $HermesHome '.env'
    if (-not (Test-Path $envFile)) { throw "no $envFile" }
    $keyLine = Select-String -Path $envFile -Pattern '^HERMES_[A-Z0-9_]*API_KEY\s*=\s*(.+)$' | Select-Object -First 1
    if (-not $keyLine) { throw 'no HERMES_*_API_KEY with a value in .env' }
    'set'
}

Check 'the dashboard finished starting' {
    # Measured, not guessed: a cold start on a clean install took 26 seconds
    # to answer -- it reads its config, opens its databases and loads its
    # profile first. Running this straight after Start-Service without
    # waiting would fail every check below on a perfectly good install.
    $deadline = (Get-Date).AddSeconds(150)
    $waited = 0
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest @web -Uri "$base/" | Out-Null
            return $(if ($waited) { "answered after ${waited}s" } else { 'answered at once' })
        } catch {
            Start-Sleep -Seconds 3
            $waited += 3
        }
    }
    throw "nothing answered on $base within 150s -- see $HermesHome\logs\service-dashboard.log"
}

Check 'the dashboard serves its page' {
    $page = Invoke-WebRequest @web -Uri "$base/"
    if ($page.Content -notmatch '(?i)<!doctype html>') { throw 'the root is not an HTML page' }
    "$([math]::Round($page.RawContentLength / 1KB)) KB of HTML"
}

Check 'its page carries a session token' {
    # This is the one check worth more than the rest. Second Brain does not
    # hold a Hermes credential: it reads the token out of this page's HTML
    # (app/hermes/rest.py) and sends it back on every call. No token, no
    # integration -- and the usual cause is a dashboard serving without its
    # web bundle, which looks like a working service from every other angle.
    $page = Invoke-WebRequest @web -Uri "$base/"
    $match = [regex]::Match($page.Content, 'window\.__HERMES_SESSION_TOKEN__\s*=\s*"([^"]+)"')
    if (-not $match.Success) {
        throw 'GET / has no window.__HERMES_SESSION_TOKEN__ -- Second Brain cannot authenticate to this Hermes'
    }
    $script:sessionToken = $match.Groups[1].Value
    'present'
}

Check 'it answers /api/status' {
    $status = Invoke-RestMethod @web -Uri "$base/api/status"
    "version $($status.version)"
}

Check 'the token opens the authenticated API' {
    if (-not $script:sessionToken) { throw 'no token was found to try' }
    $headers = @{ 'x-hermes-session-token' = $script:sessionToken }
    $active = Invoke-RestMethod @web -Uri "$base/api/profiles/active" -Headers $headers
    if ($active.name) { "active profile '$($active.name)'" } else { 'answered; no profile is active yet' }
}

Check 'the gateway left a log' {
    # A gateway with nothing to do is silent on its API but still writes.
    # An empty log after a start means it died before it got going, and the
    # service wrapper puts that output here precisely because a service has
    # no console to show it on.
    $log = Join-Path $HermesHome 'logs\service-gateway.log'
    if (-not (Test-Path $log)) { throw "no $log -- the service may not have started its child" }
    $size = (Get-Item $log).Length
    if ($size -eq 0) { throw 'the log is empty; the gateway wrote nothing at all' }
    "$([math]::Round($size / 1KB)) KB"
}

if (-not $SkipRestartCheck) {
    Check 'both come back after a restart' {
        Restart-Service -Name 'HermesGateway' -Force
        Restart-Service -Name 'HermesDashboard' -Force
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline) {
            try {
                Invoke-RestMethod @web -Uri "$base/api/status" | Out-Null
                if ((Get-Service HermesGateway).Status -eq 'Running') { return 'healthy again' }
            } catch { Start-Sleep -Seconds 3 }
        }
        throw 'they did not come back within 90s'
    }

    Check 'stopping leaves nothing behind' {
        # The reason these services wrap their child in a job object: Hermes
        # spawns children, and a stop that orphans them leaves the next start
        # fighting its own leftovers for ports and locks.
        Stop-Service -Name 'HermesGateway' -Force
        Start-Sleep -Seconds 5
        $stragglers = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
            Where-Object { $_.CommandLine -and $_.CommandLine -like '*hermes_cli.main gateway*' }
        if ($stragglers) { throw "$($stragglers.Count) hermes process(es) survived the stop" }
        Start-Service -Name 'HermesGateway'
        'no orphans'
    }
}

Write-Host ''
if ($failures -eq 0) {
    Write-Host 'All checks passed. Hermes is running and Second Brain can reach it.' -ForegroundColor Green
    exit 0
}
Write-Host "$failures check(s) failed. See DEPLOY-HERMES.md, 'When something is wrong'." -ForegroundColor Red
exit 1
