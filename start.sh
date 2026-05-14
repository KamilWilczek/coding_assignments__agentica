#!/usr/bin/env bash
set -e

echo "==> Setting up backend virtualenv..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q

echo "==> Seeding database..."
python scripts/seed_db.py
deactivate
cd ..

echo "==> Installing frontend dependencies..."
cd frontend && npm install --silent
cd ..

echo ""
echo "==> Starting backend (http://localhost:8000)..."
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

echo "==> Starting frontend (http://localhost:5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Both servers running. Open http://localhost:5173"
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
