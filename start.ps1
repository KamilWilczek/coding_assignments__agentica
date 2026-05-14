# Help Desk — single-command start (Windows PowerShell)
# Usage: .\start.ps1

$root = $PSScriptRoot

Write-Host "==> Setting up backend virtualenv..." -ForegroundColor Cyan
Push-Location "$root\backend"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -q

Write-Host "==> Seeding database..." -ForegroundColor Cyan
python scripts/seed_db.py
deactivate
Pop-Location

Write-Host "==> Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location "$root\frontend"
npm install --silent
Pop-Location

Write-Host ""
Write-Host "==> Starting backend  (http://localhost:8000) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"

Write-Host "==> Starting frontend (http://localhost:5173) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers are starting. Open http://localhost:5173 in your browser." -ForegroundColor Yellow
