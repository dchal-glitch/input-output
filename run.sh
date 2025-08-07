#!/usr/bin/env bash
# Run the FastAPI development server

echo "Starting FastAPI development server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
