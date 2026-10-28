<#
.SYNOPSIS
  Fingerprints a built release so the copy to an offline server can be proven
  complete. RUN THIS HERE, after build-release.ps1.

.DESCRIPTION
  A release reaches an air-gapped server over a channel nobody can retry
  cheaply -- a redirected RDP drive, a one-off disk. That channel can
  truncate a file without failing the copy, and a half-written wheel does not
  announce itself: it surfaces days later as an install that cannot explain
  why a package is corrupt.

  So the release carries its own manifest. This writes it here; verify.ps1's
  companion `-Manifest` switch checks it there.

  Writes TRANSFER.sha256 into the release and prints the copy command to use.
#>
[CmdletBinding()]
param(
    [string]$ReleasePath,
    # Where the release will land on the server. Printed in the copy command
    # only -- nothing here touches it.
    [string]$ServerPath = 'C:\Staging\Release'
)

$ErrorActionPreference = 'Stop'
$here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }
if (-not $ReleasePath) { $ReleasePath = Join-Path (Split-Path $here -Parent) 'Release' }
if (-not (Test-Path $ReleasePath)) { throw "No release at $ReleasePath. Run build-release.ps1 first." }

$manifestName = 'TRANSFER.sha256'
$manifestPath = Join-Path $ReleasePath $manifestName

Write-Host "`nFingerprinting $ReleasePath" -ForegroundColor Cyan
$files = Get-ChildItem -Recurse -File $ReleasePath | Where-Object { $_.Name -ne $manifestName }
$total = $files.Count
$lines = New-Object System.Collections.Generic.List[string]
$done = 0
foreach ($file in $files) {
    $relative = $file.FullName.Substring($ReleasePath.Length).TrimStart('\')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $lines.Add("$hash *$relative")
    $done++
    if ($done % 500 -eq 0) { Write-Progress -Activity 'Hashing' -Status "$done of $total" -PercentComplete ($done * 100 / $total) }
}
Write-Progress -Activity 'Hashing' -Completed
Set-Content -LiteralPath $manifestPath -Value $lines -Encoding ASCII

$bytes = ($files | Measure-Object Length -Sum).Sum
Write-Host ("    {0:N0} files, {1:N2} GB" -f $total, ($bytes / 1GB)) -ForegroundColor Green
Write-Host "    wrote $manifestName" -ForegroundColor Green

# /Z is the point: a redirected drive drops, and a restartable copy resumes
# instead of starting a multi-gigabyte transfer again.
Write-Host "`nOn the server, with this machine's drive redirected into the RDP session:" -ForegroundColor Cyan
Write-Host "    robocopy $ReleasePath $ServerPath /E /Z /R:2 /W:5" -ForegroundColor White
Write-Host "`nThen, before installing anything:" -ForegroundColor Cyan
Write-Host "    cd $ServerPath\app\deploy; .\verify.ps1 -Manifest" -ForegroundColor White
