@echo off
title Akari LIVE - Starting...
cd /d "C:\Users\PC\e-midi"

echo.
echo === Akari LIVE Setup ===
echo.

echo [1/5] OBS closing (if open)...
taskkill /IM obs64.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/5] Patching OBS scene collection...
C:\Python314\python.exe setup_obs.py
if errorlevel 1 (
    echo ERROR: setup_obs.py failed
    pause
    exit /b 1
)

echo [3/5] emotion-bus (port 8765)...
start "emotion-bus" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe -m uvicorn server.main:app --host 0.0.0.0 --port 8765"
timeout /t 3 /nobreak >nul

echo [4/5] mic-emitter + akari-house...
start "mic-emitter" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe agents\mic_emitter.py"
start "akari-house" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe -m http.server 3456 --directory akari-house-stream"

echo [5/5] Launching OBS...
timeout /t 2 /nobreak >nul
start "" "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --collection "Akari_TwitCasting_Min" --minimize-to-tray

echo.
echo === DONE ===
echo OBS is starting with emotion-overlay ready.
echo Close this window anytime.
pause