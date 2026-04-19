#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python was not found. Install Python 3.11+ and rerun setup."
  exit 1
fi

echo "=== WeGoComply Setup Script ==="
echo ""

echo "=== Setting up Backend ==="
if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "Created backend/.env. Review WEGOCOMPLY_MODE and API keys before running in live mode."
else
  echo "backend/.env already exists"
fi

if [ ! -d "$BACKEND_DIR/venv" ]; then
  echo "Creating Python virtual environment..."
  "$PYTHON_BIN" -m venv "$BACKEND_DIR/venv"
else
  echo "Python virtual environment already exists"
fi

echo "Installing backend dependencies..."
"$BACKEND_DIR/venv/bin/python" -m pip install --upgrade pip
"$BACKEND_DIR/venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"

echo ""
echo "=== Setting up Frontend ==="
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Installing Node dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
else
  echo "frontend/node_modules already exists"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Windows PowerShell:"
echo "  .\\setup.ps1"
