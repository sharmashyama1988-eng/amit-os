param()
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "  AMIT OS -- WSL2 Setup Script (Step 1 of 2)" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "  ERROR: Run as Administrator!" -ForegroundColor Red
    Write-Host "  Right-click this file -> Run as Administrator" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    Exit 1
}

Write-Host "  [1/3] Enabling WSL feature..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart 2>$null | Out-Null
Write-Host "  OK" -ForegroundColor Green

Write-Host "  [2/3] Enabling Virtual Machine Platform..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart 2>$null | Out-Null
Write-Host "  OK" -ForegroundColor Green

Write-Host "  [3/3] Setting WSL2 as default..." -ForegroundColor Yellow
wsl --set-default-version 2 2>$null
Write-Host "  OK" -ForegroundColor Green

Write-Host ""
Write-Host "  Installing Ubuntu (downloading ~500MB)..." -ForegroundColor Yellow
wsl --install -d Ubuntu

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Green
Write-Host "  WSL2 + Ubuntu installed successfully!" -ForegroundColor Green
Write-Host "  ================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Ubuntu window mein username + password set karo" -ForegroundColor White
Write-Host "  2. Ubuntu close karo" -ForegroundColor White
Write-Host "  3. BUILD-AMIT-OS.ps1 chalao (as Administrator)" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to finish"
