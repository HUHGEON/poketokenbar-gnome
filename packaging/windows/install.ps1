# Installs PokeTokenBar on Windows: the daemon, the tray app, and a login entry.
#
# Everything lands under the user's profile. Nothing here needs an
# administrator, and nothing is written outside %LOCALAPPDATA% and the
# per-user Startup folder.
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\install.ps1

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$root = Join-Path $env:LOCALAPPDATA 'PokeTokenBar'
$app  = Join-Path $root 'app'
$venv = Join-Path $root 'venv'

Write-Host "==> installing to $root"
New-Item -ItemType Directory -Force -Path $app | Out-Null
Copy-Item -Recurse -Force (Join-Path $repo 'poketokenbar') $app

Write-Host "==> creating venv"
if (-not (Test-Path $venv)) { python -m venv $venv }
$py = Join-Path $venv 'Scripts\python.exe'
& $py -m pip install --quiet --upgrade pip
# PySide6 is the tray application; orjson is an optional parsing speedup.
& $py -m pip install --quiet PySide6-Essentials
& $py -m pip install --quiet orjson

# pythonw, not python: the console host would otherwise flash a black window
# every time either process starts.
$pyw = Join-Path $venv 'Scripts\pythonw.exe'
$launchers = @{
  'poketokend.vbs' = "$pyw`" -m poketokenbar.daemon"
  'poketokenbar.vbs' = "$pyw`" -m poketokenbar.ui.app"
}
foreach ($name in $launchers.Keys) {
  $target = Join-Path $root $name
  # A .vbs shim rather than a .bat: Windows shows a console window for a batch
  # file even when what it starts has no console of its own.
  @"
Set shell = CreateObject("WScript.Shell")
shell.Environment("Process")("PYTHONPATH") = "$app"
shell.Run """$($launchers[$name])", 0, False
"@ | Set-Content -Encoding ASCII $target
  Write-Host "    wrote $target"
}

Write-Host "==> registering both at login"
$startup = [Environment]::GetFolderPath('Startup')
foreach ($name in $launchers.Keys) {
  $link = Join-Path $startup ($name -replace '\.vbs$', '.lnk')
  $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($link)
  $shortcut.TargetPath = Join-Path $root $name
  $shortcut.WorkingDirectory = $root
  $shortcut.Save()
  Write-Host "    $link"
}

Write-Host "==> starting"
foreach ($name in $launchers.Keys) {
  Start-Process -FilePath (Join-Path $root $name)
}

Write-Host ""
Write-Host "done. The companion is in the notification area."
Write-Host "state file: $env:APPDATA\poketokenbar\state.json"
