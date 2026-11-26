@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Docker Desktop ishga tushganini tekshiring.
docker info >nul 2>&1
if errorlevel 1 (
  echo XATO: Docker Desktop / Docker Engine ishga tushmagan.
  pause
  exit /b 1
)
echo Laboratoriya konteynerlarini yaratish va ishga tushirish...
docker compose up -d --build
if errorlevel 1 (
  echo XATO: docker compose up ishlamadi, xabarlarni tekshiring.
  pause
  exit /b 1
)
docker compose ps
echo.
echo Brauzer: http://127.0.0.1:8080
echo Yuklama testi: docker compose run --rm --no-deps loadtest --requests 600 --workers 20 --delay-ms 150
start "" http://127.0.0.1:8080
pause
