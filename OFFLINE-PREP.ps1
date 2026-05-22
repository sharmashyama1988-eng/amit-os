param()
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "  AMIT OS -- Offline Preparation (Step 1.5)" -ForegroundColor Cyan
Write-Host "  Downloads all packages to D:\Amit os\cache" -ForegroundColor Cyan
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

# WSL check
Write-Host "  [1/3] Checking WSL2..." -ForegroundColor Yellow
try {
    wsl --list --quiet | Out-Null
} catch {
    Write-Host "  ERROR: WSL2 not working!" -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    Exit 1
}

# Fix line endings for the prep script
Write-Host "  [2/3] Preparing scripts..." -ForegroundColor Yellow
wsl -e bash -c "sed -i 's/\r//' '/mnt/d/Amit os/build/prepare-offline.sh' && chmod +x '/mnt/d/Amit os/build/prepare-offline.sh'"

# Run prep
Write-Host "  [3/3] Downloading packages... (This may take 10-20 mins)" -ForegroundColor Yellow
Write-Host "  A folder 'cache' will be created in your project directory." -ForegroundColor Gray
Write-Host ""

wsl -u root -e bash "/mnt/d/Amit os/build/prepare-offline.sh"

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Green
Write-Host "  OFFLINE CACHE READY!" -ForegroundColor Green
Write-Host "  You can now run BUILD-AMIT-OS.ps1" -ForegroundColor Green
Write-Host "  ================================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
