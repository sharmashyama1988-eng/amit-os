@echo off
echo ===================================================
echo AMIT OS -- WSL Deep Repair Tool
echo ===================================================
echo.
echo [1/3] Enabling Windows Subsystem for Linux...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
echo.
echo [2/3] Enabling Virtual Machine Platform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
echo.
echo [3/3] Forcing WSL Kernel Update registration...
wsl --update
echo.
echo ===================================================
echo REPAIR STEPS COMPLETE!
echo.
echo IMPORTANT: Please RESTART your computer now.
echo After restart, run OFFLINE-PREP.ps1 again.
echo ===================================================
pause
