#!/bin/bash

echo "Starting FastAPI Backend..."
cd backend

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "Backend running at http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
