@echo off
chcp 65001 >nul
title Instalador - Subtitulador IA para DaVinci Resolve

set "BASE=%~dp0"
set "BASEF=%BASE:\=/%"

echo ============================================================
echo    SUBTITULADOR IA para DaVinci Resolve
echo    Instalacion automatica
echo ============================================================
echo.
echo  Esto configura el plugin en tu DaVinci Resolve.
echo  No instala nada en el sistema: todo queda en esta carpeta.
echo.

rem --- 1) Carpeta de configuracion -----------------------------------------
set "CFGDIR=%APPDATA%\SubtituladorIA"
if not exist "%CFGDIR%" mkdir "%CFGDIR%"

rem --- 2) Escribir config.json (rutas con / para evitar problemas) ----------
set "PYV=%BASEF%python/python.exe"
set "WRK=%BASEF%transcribir_worker.py"
(
  echo {
  echo   "python_venv": "%PYV%",
  echo   "worker": "%WRK%",
  echo   "idioma": "es",
  echo   "modelo": "small",
  echo   "max_caracteres": 42
  echo }
) > "%CFGDIR%\config.json"
echo  [1/2] Configuracion guardada.

rem --- 3) Copiar el plugin a la carpeta de Scripts de Resolve ---------------
set "SCRIPTS=%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility"
if not exist "%SCRIPTS%" mkdir "%SCRIPTS%"
copy /Y "%BASE%Subtitulador Text+.py" "%SCRIPTS%\" >nul
echo  [2/2] Plugin instalado en DaVinci Resolve.

echo.
echo ============================================================
echo    LISTO. Ahora abre DaVinci Resolve y ve a:
echo.
echo    Area de trabajo  -^>  Secuencias de comandos  -^>  Subtitulador Text+
echo    (Workspace -^> Scripts -^> Subtitulador Text+)
echo.
echo    IMPORTANTE: no muevas ni borres esta carpeta despues de
echo    instalar. El plugin la necesita para funcionar.
echo ============================================================
echo.
pause
