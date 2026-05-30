@echo off
REM あかりの家 配信版 起動 (port 3456)
cd /d "%~dp0.."
echo [akari-house] starting on http://localhost:3456
start "akari-house" cmd /k "python -m http.server 3456 --directory akari-house-stream"
timeout /t 2 /nobreak >nul
start "" "http://localhost:3456"
