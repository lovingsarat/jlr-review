@echo off
echo ===================================================
echo   Starting Diaspora Hub Full-Stack Web Application  
echo ===================================================
echo.

:: Check for .env file
if not exist .env (
    echo [WARNING] No .env file found in root. RAG Chatbot will show a warning until you set GEMINI_API_KEY.
    echo.
)

:: Start backend FastAPI server in a new window
echo [1/2] Launching Python backend (FastAPI) on port 8000...
start "Diaspora Hub Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn main:app --port 8000"

:: Start frontend Vite dev server in a new window
echo [2/2] Launching React frontend (Vite) on port 5173...
start "Diaspora Hub Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   Servers are launching!
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo ===================================================
echo.
pause
