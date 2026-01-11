# Run script: Starts server and 2 clients for local testing
# Usage: .\run_game.ps1

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

$ServerJob = $null
$Client1Job = $null
$Client2Job = $null

function Cleanup {
    Write-Warning "`nShutting down all processes..."

    if ($Client1Job) {
        Stop-Job -Job $Client1Job -ErrorAction SilentlyContinue
        Remove-Job -Job $Client1Job -ErrorAction SilentlyContinue
        Write-Success "Client 1 stopped"
    }

    if ($Client2Job) {
        Stop-Job -Job $Client2Job -ErrorAction SilentlyContinue
        Remove-Job -Job $Client2Job -ErrorAction SilentlyContinue
        Write-Success "Client 2 stopped"
    }

    if ($ServerJob) {
        Stop-Job -Job $ServerJob -ErrorAction SilentlyContinue
        Remove-Job -Job $ServerJob -ErrorAction SilentlyContinue
        Write-Success "Server stopped"
    }

    # Also kill any orphaned processes
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "td_server|td_client"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    Write-Success "All processes stopped"
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null
$null = Register-ObjectEvent -InputObject ([Console]) -EventName CancelKeyPress -Action {
    Cleanup
    [Environment]::Exit(0)
}

try {
    Write-Success "Starting game server and clients...`n"

    # Check for and kill any existing game processes
    $ExistingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "td_server|td_client"
    }

    if ($ExistingProcesses) {
        Write-Warning "Found existing processes, cleaning up..."
        $ExistingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }

    # Verify python is available
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "Error: python command not found"
        exit 1
    }

    Write-Warning "Starting server..."
    $ServerJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python -m server.src.td_server.main
    }
    Write-Host "Server started with Job ID: $($ServerJob.Id)"

    Write-Host "Waiting for server to initialize..."
    Start-Sleep -Seconds 2

    # Check if server is still running
    if ($ServerJob.State -eq "Failed" -or $ServerJob.State -eq "Completed") {
        Write-Error "Error: Server failed to start"
        Write-Host "Server output:"
        Receive-Job -Job $ServerJob
        Cleanup
        exit 1
    }

    Write-Success "Server is running`n"

    Write-Warning "Starting client 1..."
    $Client1Job = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python -m client.src.td_client.main
    }
    Write-Host "Client 1 started with Job ID: $($Client1Job.Id)"

    Start-Sleep -Seconds 1

    Write-Warning "Starting client 2..."
    $Client2Job = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python -m client.src.td_client.main
    }
    Write-Host "Client 2 started with Job ID: $($Client2Job.Id)"

    Write-Success "`nAll processes started!"
    Write-Host "Server Job ID: $($ServerJob.Id)"
    Write-Host "Client 1 Job ID: $($Client1Job.Id)"
    Write-Host "Client 2 Job ID: $($Client2Job.Id)"
    Write-Host "`nPress Ctrl+C to stop all processes"
    Write-Host "`nMonitoring processes... (showing output every 5 seconds)"

    # Keep the script running and show output
    while ($true) {
        Start-Sleep -Seconds 5

        # Check job states
        $ServerState = $ServerJob.State
        $Client1State = $Client1Job.State
        $Client2State = $Client2Job.State

        if ($ServerState -ne "Running") {
            Write-Error "`nServer has stopped unexpectedly!"
            Write-Host "Server output:"
            Receive-Job -Job $ServerJob
            break
        }

        # Optionally show recent output
        $ServerOutput = Receive-Job -Job $ServerJob -Keep
        $Client1Output = Receive-Job -Job $Client1Job -Keep
        $Client2Output = Receive-Job -Job $Client2Job -Keep

        if ($ServerOutput) {
            Write-Host "`n--- Server Output ---" -ForegroundColor Cyan
            Write-Host $ServerOutput[-10..-1] # Show last 10 lines
        }
    }

} catch {
    Write-Error "An error occurred: $_"
} finally {
    Cleanup
}