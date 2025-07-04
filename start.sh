#!/bin/bash

# Start script for the Research Paper Intelligence Platform

echo "Starting Research Paper Intelligence Platform..."

# Start backend
echo "Starting backend..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run build
npm start &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Backend running on http://localhost:8000"
echo "Frontend running on http://localhost:3000"

# Wait for any process to exit
wait
