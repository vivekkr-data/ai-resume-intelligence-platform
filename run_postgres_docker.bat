@echo off
cd /d %~dp0
where docker >nul 2>nul || (
  echo Docker Desktop not found or not running.
  pause
  exit /b 1
)
docker compose up --build
