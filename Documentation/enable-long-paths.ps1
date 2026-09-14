<#
.SYNOPSIS
    Enables Windows long-path support (removes the 260-character MAX_PATH
    limit) for the Second Brain vault host, and optionally runs the vault's
    log -> history migration.

.DESCRIPTION
    The vault stores notes at paths like

        <OneDrive root>\Work\Customers\<Customer>\Affiliates\<Affiliate>\
        Opportunities\<long opportunity title>\<same title again>-history.md

    which routinely exceeds Windows' classic 260-character MAX_PATH limit.
    Past that limit the failure is inconsistent and, worse, sometimes silent:

        os.rename / Move-Item        raise an error  (loud, recoverable)
        Test-Path / Path.is_file()   return FALSE    (silent, dangerous)

    The silent case is the reason this matters. A tool that asks "does this
    note exist?" is told "no" and then happily reports success having skipped
    the file entirely. On 2026-09-14 a vault migration stopped halfway through
    (26 of 58 notes) on exactly this.

    This script sets the machine-wide LongPathsEnabled policy, which lets any
    long-path-aware application (Python 3.6+, Git, .NET 4.6.2+, PowerShell)
    use full-length paths. It does NOT change or move any of the user's data.

.PARAMETER VaultPath
    The Obsidian vault root, used only for the verification step and for the
    optional migration. Defaults to the VAULT_PATH environment variable.

.PARAMETER CheckOnly
    Report the current state and exit without changing anything. Safe to run
    without administrator rights.

.PARAMETER SkipGitConfig
    Do not set Git's system-wide core.longpaths. Git has its own 260-char
    limit independent of the Windows policy, so by default this script sets
    both; pass this to leave Git alone.

.PARAMETER RunVaultMigration
    Also run the repository's log -> history vault migration after enabling
    long paths. OFF by default: that migration has already been run on this
    machine (2026-09-14) and is idempotent, so it is only useful on a host
    where it has not been run yet.

.PARAMETER RepoPath
    Second Brain repository root. Only needed with -RunVaultMigration.

.EXAMPLE
    .\enable-long-paths.ps1 -CheckOnly
    Reports the current setting. No administrator rights needed.

.EXAMPLE
    .\enable-long-paths.ps1
    Enables long paths machine-wide. Must be run as administrator.

.NOTES
    Requires administrator rights to change the setting (it is machine-wide
    policy under HKLM). A restart is recommended: already-running processes
    keep their old behaviour until restarted.

    To reverse: set the same value back to 0, or delete it. Nothing else on
    the system is modified.
#>

[CmdletBinding()]
param(
    [string] $VaultPath = $env:VAULT_PATH,
    [switch] $CheckOnly,
    [switch] $SkipGitConfig,
    [switch] $RunVaultMigration,
    [string] $RepoPath = "C:\myWorx\Projects\second_brain"
)

$ErrorActionPreference = 'Stop'

$registryPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem'
$registryName = 'LongPathsEnabled'

function Write-Step { param([string] $Text) Write-Host "`n== $Text" -ForegroundColor Cyan }
function Write-Ok   { param([string] $Text) Write-Host "   [ok]   $Text" -ForegroundColor Green }
function Write-Warn { param([string] $Text) Write-Host "   [warn] $Text" -ForegroundColor Yellow }
function Write-Info { param([string] $Text) Write-Host "   $Text" }

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-LongPathsSetting {
    $current = Get-ItemProperty -Path $registryPath -Name $registryName -ErrorAction SilentlyContinue
    if ($null -eq $current) { return $null }
    return [int] $current.$registryName
}

# --- report current state ---------------------------------------------------

Write-Step "Current state"

$isAdmin = Test-Administrator
Write-Info ("Administrator:   " + $(if ($isAdmin) { "yes" } else { "NO" }))
Write-Info ("Windows:         " + [System.Environment]::OSVersion.Version.ToString())
Write-Info ("PowerShell:      " + $PSVersionTable.PSVersion.ToString())

$before = Get-LongPathsSetting
if ($before -eq 1) {
    Write-Ok "LongPathsEnabled is already 1 (long paths allowed)"
} elseif ($null -eq $before) {
    Write-Warn "LongPathsEnabled is not set (Windows default: 260-char limit applies)"
} else {
    Write-Warn "LongPathsEnabled is $before (260-char limit applies)"
}

if (-not $SkipGitConfig) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        $gitLongPaths = (& git config --system --get core.longpaths) 2>$null
        if ($gitLongPaths -eq 'true') {
            Write-Ok "git core.longpaths is already true"
        } else {
            Write-Warn "git core.longpaths is not set (Git keeps its own 260-char limit)"
        }
    }
}

if ($CheckOnly) {
    Write-Step "Check-only mode: nothing was changed"
    exit 0
}

# --- apply ------------------------------------------------------------------

if (-not $isAdmin) {
    Write-Step "Cannot continue"
    Write-Warn "Changing this setting needs administrator rights (it is machine-wide policy)."
    Write-Info "Re-run this script from an elevated PowerShell, or run with -CheckOnly to just report."
    exit 1
}

Write-Step "Enabling long paths"

if ($before -eq 1) {
    Write-Ok "Already enabled; leaving it alone"
} else {
    # DWORD 1 on the FileSystem policy key. This is the documented, supported
    # switch (Windows 10 1607+); it grants long-path support to applications
    # that declare themselves long-path aware, and changes nothing else.
    New-ItemProperty -Path $registryPath -Name $registryName -Value 1 `
                     -PropertyType DWORD -Force | Out-Null
    $after = Get-LongPathsSetting
    if ($after -eq 1) {
        Write-Ok "LongPathsEnabled set to 1"
    } else {
        Write-Warn "Tried to set LongPathsEnabled but it now reads '$after' -- check Group Policy, which can override this key"
    }
}

if (-not $SkipGitConfig) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        & git config --system core.longpaths true
        if ($LASTEXITCODE -eq 0) { Write-Ok "git core.longpaths set to true" }
        else { Write-Warn "could not set git core.longpaths (exit $LASTEXITCODE)" }
    } else {
        Write-Info "git not found on PATH; skipping its long-path setting"
    }
}

# --- verify -----------------------------------------------------------------

Write-Step "Verifying with a real long path"

# Built under TEMP, not the vault: the check must never create stray files
# among the user's notes, and it is removed either way.
$deepRoot = Join-Path $env:TEMP ("longpath-check-" + [guid]::NewGuid().ToString("N"))
try {
    $segment = "a" * 60
    $deep = $deepRoot
    foreach ($i in 1..5) { $deep = Join-Path $deep $segment }   # ~300+ chars

    New-Item -ItemType Directory -Path $deep -Force | Out-Null
    $probe = Join-Path $deep "probe.txt"
    Set-Content -Path $probe -Value "ok" -Encoding utf8

    if (Test-Path $probe) {
        Write-Ok ("Created and read a " + $probe.Length + "-character path")
    } else {
        # The dangerous case: the write appeared to succeed but the file is
        # invisible to Test-Path. Report it loudly rather than as success.
        Write-Warn "Wrote the file but Test-Path cannot see it -- long paths are NOT in effect for this process"
    }
} catch {
    Write-Warn ("Long-path test failed: " + $_.Exception.Message)
    Write-Info "If the setting was just applied, restart the machine and re-run with -CheckOnly."
} finally {
    if (Test-Path $deepRoot) {
        # -LiteralPath and \\?\ so the cleanup itself is not defeated by the
        # very limit being tested.
        try { Remove-Item -LiteralPath ("\\?\" + $deepRoot) -Recurse -Force -ErrorAction Stop }
        catch { Write-Warn ("Could not remove the test folder; delete it manually: " + $deepRoot) }
    }
}

# --- optional: the vault migration -----------------------------------------

if ($RunVaultMigration) {
    Write-Step "Running the vault log -> history migration"

    if (-not $VaultPath) {
        Write-Warn "No -VaultPath given and VAULT_PATH is not set; skipping the migration"
    } else {
        $python = Join-Path $RepoPath "src\backend\.venv\Scripts\python.exe"
        $scripts = Join-Path $RepoPath "src\backend\app\business\core\skills\catalog\vault\create-companies-partners\scripts"
        $managers = Join-Path $RepoPath "src\backend\app\business\core\skills\managers"
        $migration = Join-Path $scripts "migrate_hub_children.py"

        if (-not (Test-Path $python))    { Write-Warn "Python not found at $python"; exit 1 }
        if (-not (Test-Path $migration)) { Write-Warn "Migration not found at $migration"; exit 1 }

        # The migration imports the shared vault_manager engine, which lives in
        # managers/ and is placed on PYTHONPATH at deploy time.
        $env:PYTHONPATH = $managers

        Write-Info "Dry run first (writes nothing):"
        & $python $migration --vault-path $VaultPath --dry-run
        Write-Host ""
        $answer = Read-Host "Apply these changes? Type YES to proceed"
        if ($answer -eq 'YES') {
            & $python $migration --vault-path $VaultPath
            Write-Ok "Migration complete (it is idempotent; re-running reports zeros)"
        } else {
            Write-Info "Skipped. Nothing was written."
        }
    }
}

Write-Step "Done"
Write-Info "A restart is recommended: processes already running keep the old behaviour."
Write-Info "To reverse: set $registryName under $registryPath back to 0."
