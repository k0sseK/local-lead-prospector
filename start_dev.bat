@echo off
setlocal

echo.
echo [1/3] Odpalanie bazy danych (PostgreSQL) w Dockerze...
docker-compose up db -d

echo.
echo [2/3] Odpalanie Backendu (FastAPI) w nowym oknie...
start "LLP Backend" cmd /k "cd backend && (if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else (call venv\Scripts\activate.bat)) && python -m pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"

echo.
echo [3/3] Odpalanie Frontendu (Nuxt) w nowym oknie...
start "LLP Frontend" cmd /k "cd frontend && pnpm dev"

echo.
echo Gotowe! 
echo - Backend: http://localhost:8000/docs
echo - Frontend: http://localhost:3000
echo.
pause
