@echo off
REM emotion-bus と mic-emitter を停止する
taskkill /FI "WindowTitle eq emotion-bus*" /F >nul 2>&1
taskkill /FI "WindowTitle eq mic-emitter*" /F >nul 2>&1
REM ポート8765を使用しているプロセスも強制終了
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765 "') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo [stop_bus] emotion-bus stopped.
