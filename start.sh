#!/bin/bash

# Chameleon Project Startup Script
echo "🚀 Starting Chameleon - Hackathon Project Stealer"
echo "=============================================="

# Check if .env file exists in backend
if [ ! -f "backend/.env" ]; then
    echo "❌ Missing backend/.env file!"
    echo "Please create backend/.env with:"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    echo "GITHUB_TOKEN=your_github_token_here"
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting FastAPI backend..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Start frontend
echo "🎨 Starting Next.js frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started successfully!"
echo "🔗 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait 