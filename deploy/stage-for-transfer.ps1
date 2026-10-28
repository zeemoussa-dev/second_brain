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
    [string]$ServerPath = 'C:\Staging\Release',
    # Pack the whole release into ONE file to carry across. Over a file share
    # that is one scan and one resumable item instead of thousands, and the
    # archive gets a hash of its own so a bad transfer is caught before
    # anything is unpacked.
    [switch]$SingleArchive
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

if ($SingleArchive) {
    # tar.exe (bsdtar) is in system32 on Windows 10 and Server 2019 onwards, so
    # it is already on both machines -- unlike 7-Zip, which would have to be
    # transferred before it could help transfer anything.
    #
    # tar rather than Compress-Archive/Expand-Archive: those are the pair that
    # fails on a tree like node_modules, where a path crosses 260 characters,
    # and it fails without saying so.
    $leaf = Split-Path $ReleasePath -Leaf
    $parent = Split-Path $ReleasePath -Parent
    $archive = Join-Path $parent "$leaf.tar.gz"
    if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }

    Write-Host "`nPacking $leaf into one file" -ForegroundColor Cyan
    $started = Get-Date
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & tar.exe -czf $archive -C $parent $leaf
        if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE." }
    } finally {
        $ErrorActionPreference = $previous
    }
    $packed = (Get-Item $archive).Length
    Write-Host ("    {0:N2} GB -> {1:N2} GB in {2:N0}s" -f ($bytes / 1GB), ($packed / 1GB), ((Get-Date) - $started).TotalSeconds) -ForegroundColor Green

    # The manifest inside proves the extracted tree; this proves the one file
    # that crosses the wire, before anyone spends minutes unpacking it.
    $archiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash
    Set-Content -LiteralPath "$archive.sha256" -Value "$archiveHash *$leaf.tar.gz" -Encoding ASCII
    Write-Host "    $archiveHash" -ForegroundColor DarkGray

    $serverParent = Split-Path $ServerPath -Parent
    Write-Host "`nCarry these two files across:" -ForegroundColor Cyan
    Write-Host "    $archive" -ForegroundColor White
    Write-Host "    $archive.sha256" -ForegroundColor White
    Write-Host "`nOn the server:" -ForegroundColor Cyan
    Write-Host "    # 1. check the file survived the copy" -ForegroundColor DarkGray
    Write-Host "    (Get-FileHash .\$leaf.tar.gz).Hash -eq (Get-Content .\$leaf.tar.gz.sha256).Split(' ')[0]" -ForegroundColor White
    Write-Host "    # 2. unpack to a SHORT path, so no file inside crosses 260 characters" -ForegroundColor DarkGray
    Write-Host "    mkdir $serverParent -Force; tar -xzf .\$leaf.tar.gz -C $serverParent" -ForegroundColor White
    Write-Host "    # 3. check every unpacked file, before installing anything" -ForegroundColor DarkGray
    Write-Host "    cd $ServerPath\app\deploy; .\verify.ps1 -Manifest" -ForegroundColor White
    return
}

# /Z is the point: any of these channels can drop, and a restartable copy
# resumes instead of starting a multi-gigabyte transfer again.
Write-Host "`nCopy it across with robocopy rather than Explorer:" -ForegroundColor Cyan
Write-Host "    robocopy $ReleasePath $ServerPath /E /Z /R:2 /W:5" -ForegroundColor White
Write-Host "`nThen, before installing anything:" -ForegroundColor Cyan
Write-Host "    cd $ServerPath\app\deploy; .\verify.ps1 -Manifest" -ForegroundColor White
