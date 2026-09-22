<#
Stops, starts and restarts this checkout's backend safely (BUG-068, BUG-070).

  tools\backend.cmd status     who holds port 8001, and whether it runs the current commit
  tools\backend.cmd stop       stops the whole backend: launcher shell, reloader and worker
  tools\backend.cmd start      refuses if port 8001 is held; otherwise starts it and waits for /health
  tools\backend.cmd restart    stop, then start -- use this after pulling framework changes

Why stopping needs more than killing "uvicorn":
- `uvicorn --reload` runs the app in a multiprocessing child that inherits the listening
  socket. Its command line says `spawn_main(parent_pid=N)`, not "uvicorn", and when the
  reloader dies it keeps serving whatever code it loaded -- while Windows still reports the
  dead reloader's PID as the port's owner (BUG-068).
- The launcher shell (`cmd /c run-backend.cmd > backend.log`) survives its uvicorn and keeps
  the log open, so the next launch cannot open the log and starts nothing (BUG-070).

A process on port 8001 that is not a Second Brain backend is never stopped; it is named.
Only one framework checkout per machine can serve port 8001, so a launcher or uvicorn
running `app.main:app` is taken to be this checkout's.
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('status', 'stop', 'start', 'restart', 'preflight')]
    [string]$Command = 'status'
)

$ErrorActionPreference = 'Stop'
$Port = 8001
$HealthUrl = "http://127.0.0.1:$Port/health"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BackendDir = Join-Path $RepoRoot 'src\backend'
$RunBackend = Join-Path $PSScriptRoot 'run-backend.cmd'

function Write-Note([string]$Text) { Write-Host "[Second Brain] $Text" }

function Get-AllProcesses {
    Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine
}

function Get-PortOwnerId {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $listener) { return $null }
    return [int]$listener.OwningProcess
}

function Get-SpawnParentId($Process) {
    if ($Process.CommandLine -match 'spawn_main\(parent_pid=(\d+)') { return [int]$Matches[1] }
    return $null
}

function Test-IsBackendRoot($Process) {
    $line = [string]$Process.CommandLine
    if ($Process.Name -eq 'cmd.exe' -and $line -match 'run-backend\.cmd') { return $true }
    if ($Process.Name -in @('python.exe', 'uvicorn.exe') -and $line -match 'uvicorn' -and $line -match 'app\.main:app') { return $true }
    return $false
}

# Every process belonging to the backend: launcher shells, uvicorn reloaders, and their
# workers -- including a worker whose reloader is gone, found through the parent_pid in its
# own command line, or through the dead PID Windows still names as the port's owner.
function Get-BackendProcesses {
    $all = @(Get-AllProcesses)
    $alive = @{}
    foreach ($process in $all) { $alive[[int]$process.ProcessId] = $process }

    $members = @{}
    foreach ($process in $all) {
        if (Test-IsBackendRoot $process) { $members[[int]$process.ProcessId] = $process }
    }
    $ownerId = Get-PortOwnerId
    $deadOwnerIds = @()
    if ($null -ne $ownerId -and -not $alive.ContainsKey($ownerId)) { $deadOwnerIds += $ownerId }

    do {
        $added = $false
        foreach ($process in $all) {
            $id = [int]$process.ProcessId
            if ($members.ContainsKey($id)) { continue }
            $spawnParent = Get-SpawnParentId $process
            $childOfMember = $members.ContainsKey([int]$process.ParentProcessId)
            $workerOfMember = $null -ne $spawnParent -and ($members.ContainsKey($spawnParent) -or $deadOwnerIds -contains $spawnParent)
            if ($childOfMember -or $workerOfMember) {
                $members[$id] = $process
                $added = $true
            }
        }
    } while ($added)

    return @($members.Values)
}

function Get-Role($Process) {
    if ($Process.Name -eq 'cmd.exe') { return 'launcher shell' }
    if ($null -ne (Get-SpawnParentId $Process)) { return 'worker' }
    if ([string]$Process.CommandLine -match 'uvicorn') { return 'uvicorn' }
    return $Process.Name
}

function Get-CheckoutCommit {
    try {
        $commit = & git -C $RepoRoot rev-parse HEAD 2>$null
        if ($LASTEXITCODE -eq 0) { return ([string]$commit).Trim() }
    } catch { }
    return $null
}

function Get-Health {
    try { return Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3 } catch { return $null }
}

function Describe-PortOwner([int]$OwnerId) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$OwnerId" -ErrorAction SilentlyContinue
    if ($null -eq $process) { return "pid $OwnerId (no longer running -- a worker it started holds the socket)" }
    return "pid $OwnerId $($process.Name): $($process.CommandLine)"
}

# -- commands --------------------------------------------------------------------------------

function Invoke-Status {
    $ownerId = Get-PortOwnerId
    if ($null -eq $ownerId) { Write-Note "port $Port is free -- no backend is running" }
    else { Write-Note "port $Port is held by $(Describe-PortOwner $ownerId)" }

    foreach ($process in (Get-BackendProcesses | Sort-Object ProcessId)) {
        Write-Note ("  {0,-15} pid {1}" -f (Get-Role $process), $process.ProcessId)
    }

    $health = Get-Health
    if ($null -eq $health) { if ($null -ne $ownerId) { Write-Note "/health does not answer" }; return 0 }
    $checkout = Get-CheckoutCommit
    Write-Note "/health: version $($health.version), running commit $($health.commit)"
    if ($checkout -and $health.commit -and $health.commit -ne $checkout) {
        Write-Note "STALE: the checkout is at $checkout. Run: tools\backend.cmd restart"
        return 1
    }
    return 0
}

function Invoke-Stop {
    $members = @(Get-BackendProcesses)
    $ownerId = Get-PortOwnerId
    $memberIds = @($members | ForEach-Object { [int]$_.ProcessId })

    if ($null -ne $ownerId -and $memberIds -notcontains $ownerId -and $members.Count -eq 0) {
        Write-Note "port $Port is held by $(Describe-PortOwner $ownerId)"
        Write-Note "that is not a Second Brain backend, so it was left alone. Stop it yourself, then start."
        return 1
    }
    if ($members.Count -eq 0) { Write-Note "no backend is running"; return 0 }

    foreach ($process in ($members | Sort-Object ProcessId)) {
        # Stopping an earlier tree may already have taken this one.
        if ($null -eq (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) { continue }
        Write-Note ("stopping {0,-15} pid {1}" -f (Get-Role $process), $process.ProcessId)
        # Through cmd: in Windows PowerShell a native command's stderr becomes a terminating
        # error under 'Stop', and taskkill reports a child that went with its parent there.
        & cmd.exe /c "taskkill /PID $($process.ProcessId) /T /F >nul 2>&1"
    }

    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        if ($null -eq (Get-PortOwnerId) -and @(Get-BackendProcesses).Count -eq 0) {
            Write-Note "stopped; port $Port is free"
            return 0
        }
        Start-Sleep -Milliseconds 500
    }
    $ownerId = Get-PortOwnerId
    if ($null -ne $ownerId) { Write-Note "port $Port is still held by $(Describe-PortOwner $ownerId)" }
    else { Write-Note "some backend processes did not exit: $((@(Get-BackendProcesses) | ForEach-Object { $_.ProcessId }) -join ', ')" }
    return 1
}

function Invoke-Preflight {
    $ownerId = Get-PortOwnerId
    if ($null -eq $ownerId) { return 0 }
    Write-Note "port $Port is already held by $(Describe-PortOwner $ownerId)"
    if (@(Get-BackendProcesses).Count -eq 0) {
        Write-Note "that is not a Second Brain backend. Stop it yourself, then start."
        return 1
    }
    $health = Get-Health
    if ($null -ne $health) { Write-Note "it answers /health as version $($health.version), commit $($health.commit)" }
    Write-Note "not starting a second backend. To replace it: tools\backend.cmd restart"
    return 1
}

# The backend writes to src\backend\backend.log. If an old launcher still holds that file,
# a redirect into it fails before anything starts and nothing says why (BUG-070), so fall
# back to a fresh file and say so.
function Get-WritableLog {
    $log = Join-Path $BackendDir 'backend.log'
    try {
        $stream = [System.IO.File]::Open($log, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $stream.Close()
        return $log
    } catch {
        $fallback = Join-Path $BackendDir ("backend-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
        Write-Note "backend.log is held open by another process; logging to $fallback instead"
        return $fallback
    }
}

function Invoke-Start {
    if ((Invoke-Preflight) -ne 0) { return 1 }
    if (-not (Test-Path (Join-Path $BackendDir '.venv\Scripts\uvicorn.exe'))) {
        Write-Note "the backend venv is missing -- see Deployment.md section 3"
        return 1
    }

    $log = Get-WritableLog
    $launcher = Start-Process -FilePath 'cmd.exe' -WindowStyle Hidden -PassThru `
        -ArgumentList "/c `"`"$RunBackend`" > `"$log`" 2>&1`""
    Write-Note "starting (launcher pid $($launcher.Id)); log: $log"

    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        $health = Get-Health
        if ($null -ne $health) {
            $checkout = Get-CheckoutCommit
            Write-Note "up on http://localhost:$Port -- version $($health.version), commit $($health.commit)"
            if ($checkout -and $health.commit -and $health.commit -ne $checkout) {
                Write-Note "WARNING: it reports commit $($health.commit), but the checkout is at $checkout"
                return 1
            }
            return 0
        }
        if ($launcher.HasExited) {
            Write-Note "the backend exited before answering /health. Last lines of $($log):"
            if (Test-Path $log) { Get-Content $log -Tail 20 | ForEach-Object { Write-Host "    $_" } }
            return 1
        }
        Start-Sleep -Seconds 1
    }
    Write-Note "no answer from /health after 90s; see $log"
    return 1
}

switch ($Command) {
    'status'    { exit (Invoke-Status) }
    'stop'      { exit (Invoke-Stop) }
    'start'     { exit (Invoke-Start) }
    'preflight' { exit (Invoke-Preflight) }
    'restart'   {
        if ((Invoke-Stop) -ne 0) { exit 1 }
        exit (Invoke-Start)
    }
}
