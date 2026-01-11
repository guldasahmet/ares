@echo off
TITLE ARES System Launcher
COLOR 0B

echo ==================================================
echo   ARES - Multi-Agent Tactical Command System
echo ==================================================
echo.

echo [1/2] TileServer (Harita) Baslatiliyor...
cd assets
:: DÜZELTME: 'npx' ekledik. Bu sayede PATH hatasi almadan calisir.
start "TileServer" cmd /k "npx tileserver-gl-light gokce_ada.mbtiles"
cd ..
timeout /t 5 >nul

echo [2/2] Simulasyon Server (Flask + Mavlink) Baslatiliyor...
start "ARES Server" cmd /k "python sim/server.py"
timeout /t 2 >nul

echo [3/3] Arayuz (UI) Baslatiliyor...
start "ARES Interface" cmd /k "python main.py"

echo.
echo TUM SISTEMLER AKTIF!
exit