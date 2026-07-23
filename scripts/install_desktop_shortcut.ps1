param(
    [string]$TargetPath = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not $TargetPath) {
    $TargetPath = Join-Path $root "dist\DeatonAutoImageStudio.exe"
}
if (-not (Test-Path $TargetPath)) {
    throw "EXE not found: $TargetPath. Run scripts\build_windows.ps1 first."
}

$desktop = [Environment]::GetFolderPath("Desktop")
$linkPath = Join-Path $desktop "Deaton Auto Image Studio.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($linkPath)
$shortcut.TargetPath = (Resolve-Path $TargetPath)
$shortcut.WorkingDirectory = Split-Path $TargetPath
$shortcut.IconLocation = "$TargetPath,0"
$shortcut.Description = "Deaton Auto local image case studio"
$shortcut.Save()

Write-Host "Desktop shortcut created: $linkPath"
