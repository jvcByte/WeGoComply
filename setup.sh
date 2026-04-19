#!/bin/bash

echo "=== WeGoComply Setup Script ==="
echo ""

# Install pip if not available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# Backend setup
echo ""
echo "=== Setting up Backend ==="
cd backend

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please add your API keys before running."
fi

# Install Python dependencies
if pip3 show fastapi &> /dev/null; then
    echo "Python dependencies already installed. Skipping..."
else
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

cd ..

# Frontend setup
echo ""
echo "=== Setting up Frontend ==="
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo "Node modules already installed."
fi

cd ..

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To run the project:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  uvicorn main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
