# ============================================================
#  Instalador del Subtitulador IA para DaVinci Resolve (Windows)
#  Ejecutar en PowerShell:  .\instalar.ps1
# ============================================================
$ErrorActionPreference = "Stop"
$base = $PSScriptRoot
Write-Host "== Subtitulador IA - Instalador ==" -ForegroundColor Cyan

# 1) Comprobar Python 3.13 --------------------------------------------------
Write-Host "`n[1/5] Buscando Python 3.13..." -ForegroundColor Yellow
$usarLauncher = $false
$python = $null

# Preferimos el administrador 'py' con la version 3.13 exacta
try {
    $v = & py -V:3.13 --version 2>&1
    if ($v -match "Python 3\.13") { $usarLauncher = $true }
} catch {}

if (-not $usarLauncher) {
    # Alternativa: un python.exe suelto en el PATH que sea 3.9+
    foreach ($cmd in @("python", "python3")) {
        try {
            $v = & $cmd --version 2>&1
            if ($v -match "Python 3\.(9|1[0-3])") { $python = $cmd; break }
        } catch {}
    }
}

if (-not $usarLauncher -and -not $python) {
    Write-Host "  No encontre Python 3.13." -ForegroundColor Red
    Write-Host "  Instalalo con:  py install 3.13" -ForegroundColor Red
    Write-Host "  Luego vuelve a ejecutar este script."
    exit 1
}
if ($usarLauncher) {
    Write-Host "  OK: $(& py -V:3.13 --version)  (via administrador 'py')" -ForegroundColor Green
} else {
    Write-Host "  OK: $(& $python --version)" -ForegroundColor Green
}

# 2) Crear entorno virtual --------------------------------------------------
Write-Host "`n[2/5] Creando entorno virtual (venv)..." -ForegroundColor Yellow
$venv = Join-Path $base "venv"
if (-not (Test-Path $venv)) {
    if ($usarLauncher) {
        & py -V:3.13 -m venv $venv
    } else {
        & $python -m venv $venv
    }
}
$pyVenv = Join-Path $venv "Scripts\python.exe"
Write-Host "  OK: $pyVenv" -ForegroundColor Green

# 3) Instalar faster-whisper ------------------------------------------------
Write-Host "`n[3/5] Instalando faster-whisper (puede tardar unos minutos)..." -ForegroundColor Yellow
& $pyVenv -m pip install --upgrade pip | Out-Null
& $pyVenv -m pip install faster-whisper
Write-Host "  OK: faster-whisper instalado" -ForegroundColor Green

# 4) Generar config.json ----------------------------------------------------
Write-Host "`n[4/5] Guardando configuracion..." -ForegroundColor Yellow
$cfgDir = Join-Path $env:APPDATA "SubtituladorIA"
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$config = @{
    python_venv    = $pyVenv
    worker         = (Join-Path $base "transcribir_worker.py")
    idioma         = "es"        # es / en / auto
    modelo         = "small"     # tiny, base, small, medium, large-v3
    max_caracteres = 42
} | ConvertTo-Json
# Escribir SIN BOM para que Python lo lea sin problemas
$sinBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $cfgDir "config.json"), $config, $sinBom)
Write-Host "  OK: $cfgDir\config.json" -ForegroundColor Green

# 5) Copiar el plugin a la carpeta de Scripts de Resolve --------------------
Write-Host "`n[5/5] Instalando el plugin dentro de DaVinci Resolve..." -ForegroundColor Yellow
$scriptsDir = Join-Path $env:APPDATA "Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility"
New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
Copy-Item (Join-Path $base "Subtitulador_IA.py") -Destination $scriptsDir -Force
Write-Host "  OK: copiado a $scriptsDir" -ForegroundColor Green

Write-Host "`n== Instalacion completa ==" -ForegroundColor Cyan
Write-Host "Abre DaVinci Resolve, abre un timeline y ve a:" -ForegroundColor White
Write-Host "   Workspace -> Scripts -> Subtitulador_IA" -ForegroundColor Green
