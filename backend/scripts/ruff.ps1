# Run Ruff format + lint from backend/ (PowerShell).
# Works even if the terminal was open before `winget install astral-sh.ruff`.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot/..

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
        [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Resolve-Ruff {
    Refresh-Path

    $cmd = Get-Command ruff -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\ruff.exe"
        "$PSScriptRoot\..\.venv\Scripts\ruff.exe"
    )

    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return (Resolve-Path $path).Path
        }
    }

    $wingetPackage = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" `
        -Filter "ruff.exe" -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    if ($wingetPackage) {
        return $wingetPackage
    }

    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        return "python -m ruff"
    }

    throw @"
'ruff' is not available.

Option A (no Python needed):
  winget install astral-sh.ruff
  Close and reopen this terminal, then run:
    .\scripts\ruff.ps1

Option B (venv):
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements-dev.txt
  .\scripts\ruff.ps1
"@
}

function Invoke-Ruff {
    param([string]$Ruff, [string[]]$RuffArgs)
    if ($Ruff -eq "python -m ruff") {
        & python -m ruff @RuffArgs
    } else {
        & $Ruff @RuffArgs
    }
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$ruff = Resolve-Ruff
Write-Host ">> using: $ruff"

Write-Host ">> ruff format ."
Invoke-Ruff -Ruff $ruff -RuffArgs @("format", ".")

Write-Host ">> ruff check . --fix"
Invoke-Ruff -Ruff $ruff -RuffArgs @("check", ".", "--fix")

Write-Host ">> ruff check ."
Invoke-Ruff -Ruff $ruff -RuffArgs @("check", ".")

Write-Host "Done."
