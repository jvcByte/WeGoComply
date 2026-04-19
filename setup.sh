#!/bin/bash

set -e  # Exit on any error

# Cleanup function to revert changes on failure
cleanup() {
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Setup failed! Reverting changes..."
        if [ -d "backend/venv" ]; then
            rm -rf backend/venv
            echo "Removed backend/venv"
        fi
        if [ -f "backend/.env" ] && [ ! -f "backend/.env.backup" ]; then
            rm -f backend/.env
            echo "Removed backend/.env"
        fi
        exit 1
    fi
}

trap cleanup EXIT

echo "=== WeGoComply Setup Script ==="
echo ""

# Backend setup
echo "=== Setting up Backend ==="
cd backend

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file. Please add your API keys before running."
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if python -c "import fastapi" 2>/dev/null; then
    echo "✓ Python dependencies already installed"
else
    echo "Installing Python dependencies in virtual environment..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✓ Python dependencies installed"
fi

deactivate
cd ..

# Frontend setup
echo ""
echo "=== Setting up Frontend ==="
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
    echo "✓ Node dependencies installed"
else
    echo "✓ Node modules already installed"
fi

cd ..

echo ""
echo "=== ✓ Setup Complete! ==="
echo ""
echo "To run the project:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
echo ""
echo "Note: Backend runs in a virtual environment (venv)"
