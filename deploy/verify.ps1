<#
.SYNOPSIS
  Checks that an installed Second Brain is really serving, from the server.

.DESCRIPTION
  Tests are not shipped in the release -- the package carries the code, not
  the development lifecycle -- so this is how an installed app is checked.
  It makes real HTTP requests to the running service and reports what it
  found, rather than asserting that the install script finished.

  Safe to run at any time: every request is a read.
#>
[CmdletBinding()]
param(
    [int]$Port = 443,
    [string]$ServerName = 'localhost',
    # A company certificate issued for the server's real name will not match
    # `localhost`, and a self-signed one is not in this machine's trust store
    # yet. Neither says the app is broken, so checking from the box itself
    # ignores trust by default.
    [switch]$RequireValidCertificate,
    # Checks the COPIED FILES against the manifest stage-for-transfer.ps1
    # wrote, then stops. Run this before installing anything: a transfer that
    # truncated a file does not announce it, and the install built on it fails
    # much later and somewhere else.
    [switch]$Manifest,
    # How long a cold start is given to answer before this reports a failure.
    # Generous on purpose: the first start reads the whole vault, and how long
    # that takes is a property of the vault, not of the install.
    [int]$StartupTimeoutSeconds = 180,
    # Inferred from the port, which is right for the two ports this is
    # installed on, and wrong for anything else. Override it rather than be
    # told the install is broken because the checks spoke https to an http
    # server.
    [ValidateSet('http', 'https')][string]$Scheme
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }

if ($Manifest) {
    # This script lives at <release>\app\deploy, so the release root is two up.
    $releaseRoot = Split-Path (Split-Path $here -Parent) -Parent
    $manifestPath = Join-Path $releaseRoot 'TRANSFER.sha256'
    if (-not (Test-Path $manifestPath)) {
        throw "No TRANSFER.sha256 at $releaseRoot. The build machine writes it with stage-for-transfer.ps1; without it there is nothing to check the copy against."
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

$scheme = if ($Scheme) { $Scheme } elseif ($Port -eq 80) { 'http' } else { 'https' }
$base = "${scheme}://${ServerName}:${Port}"
$failures = 0

function Check([string]$what, [scriptblock]$test) {
    try {
        $detail = & $test
        Write-Host ("  ok   {0}{1}" -f $what.PadRight(42), $detail) -ForegroundColor Green
    } catch {
        $script:failures++
        Write-Host ("  FAIL {0}{1}" -f $what.PadRight(42), $_.Exception.Message) -ForegroundColor Red
    }
}

$web = @{ UseBasicParsing = $true; TimeoutSec = 20 }
if (-not $RequireValidCertificate -and $scheme -eq 'https') {
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        $web.SkipCertificateCheck = $true
    } else {
        # Windows PowerShell 5.1 has no -SkipCertificateCheck: it arrived in
        # PowerShell 6. Windows Server ships 5.1, and a server with no
        # internet cannot install 7 -- so this branch is the one that
        # actually runs on the machine this script exists for. Passing the
        # parameter there fails EVERY https check with "a parameter cannot be
        # found", on an install that is working perfectly.
        [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        # 5.1 can still negotiate down to TLS 1.0, which a current server will
        # refuse outright.
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    }
}

Write-Host "`nChecking $base" -ForegroundColor Cyan

Check 'the service is running' {
    $service = Get-Service -Name 'SecondBrain' -ErrorAction Stop
    if ($service.Status -ne 'Running') { throw "service is $($service.Status)" }
    "status $($service.Status), starts $((Get-CimInstance Win32_Service -Filter "Name='SecondBrain'").StartMode)"
}

Check 'it answers /health' {
    # Polled, not asked once. A cold start reads the vault and builds its
    # index before the first request is served, so running this straight after
    # Start-Service -- which is exactly what the runbook says to do -- would
    # fail on an install that is merely still starting. Every check below
    # assumes a server that is up, so this is the one that waits.
    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    $lastProblem = 'no attempt made'
    $waited = 0
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod @web -Uri "$base/health"
            if ($health.status -ne 'ok') { throw "status was '$($health.status)'" }
            $detail = "version $($health.version), commit $($health.commit.Substring(0,8))"
            if ($waited -gt 0) { $detail += ", answered after $waited" + 's' }
            return $detail
        } catch {
            $lastProblem = $_.Exception.Message
            Start-Sleep -Seconds 3
            $waited += 3
        }
    }
    throw "no answer in $StartupTimeoutSeconds" + "s. Last: $lastProblem"
}

Check 'the web interface is served' {
    $page = Invoke-WebRequest @web -Uri "$base/"
    if ($page.Content -notmatch '(?i)<!doctype html>') { throw 'the root is not an HTML page' }
    "$([math]::Round($page.RawContentLength / 1KB)) KB of HTML"
}

Check 'its code loads' {
    $page = Invoke-WebRequest @web -Uri "$base/"
    $bundle = ([regex]'src="(/assets/[^"]+\.js)"').Match($page.Content).Groups[1].Value
    if (-not $bundle) { throw 'the page references no bundle' }
    $asset = Invoke-WebRequest @web -Uri "$base$bundle"
    "$([math]::Round($asset.RawContentLength / 1KB)) KB of JavaScript"
}

Check 'a deep link reloads into the app' {
    $page = Invoke-WebRequest @web -Uri "$base/browse/anything"
    if ($page.Content -notmatch '(?i)<!doctype html>') { throw 'a deep link did not return the app' }
    'serves the app, not a 404'
}

Check 'the API refuses an anonymous caller' {
    try {
        Invoke-RestMethod @web -Uri "$base/vault-search/notes"
        throw 'the API answered without an account -- STOP AND INVESTIGATE'
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw $_ }
        '401, as it should'
    }
}

if ($scheme -eq 'https') {
    Check 'the certificate is the one you expect' {
        $request = [Net.HttpWebRequest]::Create("$base/health")
        $request.ServerCertificateValidationCallback = { $true }
        $request.GetResponse().Dispose()
        $certificate = $request.ServicePoint.Certificate
        "subject $($certificate.Subject), expires $(([datetime]$certificate.GetExpirationDateString()).ToString('yyyy-MM-dd'))"
    }
}

Check 'it comes back after a restart' {
    Restart-Service -Name 'SecondBrain' -Force
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        try {
            if ((Invoke-RestMethod @web -Uri "$base/health").status -eq 'ok') { return 'healthy again' }
        } catch { Start-Sleep -Seconds 2 }
    }
    throw 'it did not come back within 60s'
}

Write-Host ''
if ($failures -eq 0) {
    Write-Host 'All checks passed. The install is serving.' -ForegroundColor Green
    exit 0
}
Write-Host "$failures check(s) failed. See DEPLOY.md, 'When something is wrong'." -ForegroundColor Red
exit 1
