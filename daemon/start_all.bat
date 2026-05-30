@echo off
title あかりLIVE 起動中
cd /d "C:\Users\PC\e-midi"

echo.
echo =========================================
echo   あかりLIVE 配信前セットアップ
echo =========================================
echo.

echo [1/3] emotion-bus (port 8765) 起動...
start "emotion-bus" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe -m uvicorn server.main:app --host 0.0.0.0 --port 8765"

echo     3秒待ちます...
timeout /t 3 /nobreak >nul

echo [2/3] mic-emitter 起動...
start "mic-emitter" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe agents\mic_emitter.py"

echo [3/3] あかりの家 (port 3456) 起動...
start "akari-house" cmd /k "cd /d C:\Users\PC\e-midi && C:\Python314\python.exe -m http.server 3456 --directory akari-house-stream"

echo.
echo =========================================
echo  起動完了！3つの黒いウィンドウが開いてたらOK
echo.
echo  OBS overlay : http://localhost:8765/overlay
echo  あかりの家  : http://localhost:3456
echo  health      : http://localhost:8765/health
echo =========================================
echo.
echo このウィンドウは閉じていいよ。
pause
