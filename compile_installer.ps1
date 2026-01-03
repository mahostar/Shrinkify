# Shrinkify Installer Compiler Helper
# Automatically adds exclusion to prevent "EndUpdateResource failed (5)"

$BuildDir = Join-Path $PSScriptRoot "installer_build"
$IssFile = Join-Path $PSScriptRoot "Shrinkify.iss"
$Compiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   SHRINKIFY INSTALLER COMPILER " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Clean previous build
if (Test-Path $BuildDir) {
    Write-Host "[CLEAN] Removing previous build folder..." -ForegroundColor Yellow
    Remove-Item -Path $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 2. Check Admin & Add Exclusion
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARN] VS Code is NOT running as Administrator." -ForegroundColor Yellow
    Write-Host "       We cannot automatically exclude the build folder from Windows Defender." -ForegroundColor Yellow
    Write-Host "       The build MIGHT fail with 'EndUpdateResource' error." -ForegroundColor Yellow
    Write-Host "       RECOMMENDATION: Open a new PowerShell as Administrator and run this script." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} else {
    Write-Host "[SEC] Attempting to add Windows Defender Exclusion for build folder..." -ForegroundColor Gray
    try {
        Add-MpPreference -ExclusionPath $BuildDir -ErrorAction Stop
        Write-Host "[OK] Exclusion added successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "[ERR] Failed to add exclusion: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. Compile
if (Test-Path $Compiler) {
    Write-Host "[BUILD] Starting Inno Setup Compiler..." -ForegroundColor Cyan
    & $Compiler $IssFile
}
else {
    Write-Host "[ERR] ISCC.exe not found at default location!" -ForegroundColor Red
}

Write-Host "==========================================" -ForegroundColor Cyan
if (Test-Path "$BuildDir\Shrinkify_Setup_v1.exe") {
    Write-Host "SUCCESS! Installer created at:" -ForegroundColor Green
    Write-Host "$BuildDir\Shrinkify_Setup_v1.exe"
}
else {
    Write-Host "BUILD FAILED." -ForegroundColor Red
}
Write-Host "==========================================" -ForegroundColor Cyan
