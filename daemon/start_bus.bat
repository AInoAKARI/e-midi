@echo off
REM ======================================================
REM  E-MIDI emotion-bus + mic emitter 常駐起動スクリプト
REM  配信前に実行。2ウィンドウが開く。
REM  停止: stop_bus.bat を実行
REM ======================================================
cd /d "%~dp0.."

echo [emotion-bus] starting FastAPI server...
start "emotion-bus" cmd /k "python -m uvicorn server.main:app --host 0.0.0.0 --port 8765 --reload"

timeout /t 3 /nobreak >nul

echo [mic-emitter] starting mic audio emitter...
start "mic-emitter" cmd /k "python agents\mic_emitter.py --url http://localhost:8765/api/emotion"

echo.
echo emotion-bus:  http://localhost:8765
echo health check: http://localhost:8765/health
echo visualizer:   http://localhost:8765/
echo.
echo OBS overlay URL: http://localhost:8765/overlay (after Phase-2 deploy)
pause
