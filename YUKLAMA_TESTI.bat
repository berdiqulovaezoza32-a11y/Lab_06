@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 600 ta HTTP so'rov / 20 parallel ulanish / 150 ms ish...
docker compose run --rm --no-deps loadtest --requests 600 --workers 20 --delay-ms 150
pause
