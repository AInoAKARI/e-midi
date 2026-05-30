@echo off
REM ======================================================
REM  あかりLIVE — 配信前一発起動スクリプト
REM  ダブルクリック1回で全部立ち上がる
REM ======================================================
cd /d "%~dp0.."

echo [emotion-bus] FastAPI server 起動中...
start "emotion-bus" cmd /k "python -m uvicorn server.main:app --host 0.0.0.0 --port 8765"

timeout /t 3 /nobreak >nul

echo [mic-emitter] マイク音声 emitter 起動中...
start "mic-emitter" cmd /k "python agents\mic_emitter.py --url http://localhost:8765/api/emotion"

echo [akari-house] あかりの家 配信版 起動中...
start "akari-house" cmd /k "python -m http.server 3456 --directory akari-house-stream"

timeout /t 2 /nobreak >nul

echo.
echo =============================================
echo  配信準備 完了！
echo  OBS overlay URL : http://localhost:8765/overlay
echo  あかりの家      : http://localhost:3456
echo  health check    : http://localhost:8765/health
echo =============================================
echo  停止するには stop_bus.bat を実行してね
echo =============================================
