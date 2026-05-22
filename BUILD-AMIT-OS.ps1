param()
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "  AMIT OS -- ISO Builder (Step 2 of 2)" -ForegroundColor Cyan
Write-Host "  Fast - Secure - Beautiful" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "  ERROR: Run as Administrator!" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    Exit 1
}
Write-Host "  [OK] Running as Administrator" -ForegroundColor Green

# WSL check
Write-Host "  [1/5] Checking WSL2..." -ForegroundColor Yellow
$wslOk = $false
try {
    $wslList = wsl --list --quiet 2>$null
    $wslOk = $true
} catch {}

if (-not $wslOk) {
    Write-Host "  ERROR: WSL2 not found!" -ForegroundColor Red
    Write-Host "  Run STEP1-INSTALL-WSL2.ps1 first" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    Exit 1
}
Write-Host "  [OK] WSL2 available" -ForegroundColor Green

# Paths
$ProjectDir  = "D:\Amit os"
$OutputDir   = "$ProjectDir\output"
$BuildScript = "$ProjectDir\build\wsl-build.sh"
$wslScript   = "/mnt/d/Amit os/build/wsl-build.sh"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Verify files
Write-Host "  [2/5] Checking project files..." -ForegroundColor Yellow
if (-not (Test-Path $BuildScript)) {
    Write-Host "  ERROR: Build script not found: $BuildScript" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    Exit 1
}
Write-Host "  [OK] Project files found" -ForegroundColor Green

# Disk space
Write-Host "  [3/5] Checking disk space (need 8GB free on D:)..." -ForegroundColor Yellow
$disk   = Get-PSDrive D
$freeGB = [math]::Round($disk.Free / 1GB, 1)
if ($freeGB -lt 6) {
    Write-Host "  ERROR: Not enough space. Have $freeGB GB, need 8 GB" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    Exit 1
}
Write-Host "  [OK] $freeGB GB free on D:" -ForegroundColor Green

# Fix line endings
Write-Host "  [4/5] Fixing script line endings..." -ForegroundColor Yellow
wsl -e bash -c "sed -i 's/\r//' '/mnt/d/Amit os/build/wsl-build.sh' && chmod +x '/mnt/d/Amit os/build/wsl-build.sh'"
Write-Host "  [OK] Line endings fixed" -ForegroundColor Green

# Build
Write-Host ""
Write-Host "  [5/5] BUILDING AMIT OS ISO..." -ForegroundColor Green
Write-Host "  Estimated time: 20-40 minutes" -ForegroundColor Yellow
Write-Host "  Do NOT close this window!" -ForegroundColor Yellow
Write-Host "  Log: D:\Amit os\output\build.log" -ForegroundColor Gray
Write-Host ""

wsl -u root -e bash "/mnt/d/Amit os/build/wsl-build.sh"

# Result
$isoPath = "$OutputDir\amit-os-1.0-amd64.iso"
if (Test-Path $isoPath) {
    $sizeMB = [math]::Round((Get-Item $isoPath).Length / 1MB, 0)
    Write-Host ""
    Write-Host "  ================================================" -ForegroundColor Green
    Write-Host "  AMIT OS ISO READY!" -ForegroundColor Green
    Write-Host "  ================================================" -ForegroundColor Green
    Write-Host "  File : D:\Amit os\output\amit-os-1.0-amd64.iso" -ForegroundColor White
    Write-Host "  Size : $sizeMB MB" -ForegroundColor White
    Write-Host ""
    Write-Host "  HOW TO USE IN VM:" -ForegroundColor Cyan
    Write-Host "  1. Open VirtualBox or VMware" -ForegroundColor White
    Write-Host "  2. New VM -> Linux -> Debian 64-bit" -ForegroundColor White
    Write-Host "  3. RAM: 4096 MB, Storage: 20 GB" -ForegroundColor White
    Write-Host "  4. Mount ISO -> Boot!" -ForegroundColor White
    Write-Host "  ================================================" -ForegroundColor Green
    Write-Host ""
    Start-Process explorer.exe $OutputDir
} else {
    Write-Host ""
    Write-Host "  BUILD FAILED! Check log:" -ForegroundColor Red
    Write-Host "  $OutputDir\build.log" -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"
