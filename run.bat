@echo off
REM Run the FastAPI development server on Windows

echo Starting FastAPI development server...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
