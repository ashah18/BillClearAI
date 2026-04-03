#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${BOLD}${CYAN}[billclear]${RESET} $*"; }
ok()   { echo -e "${GREEN}  ✓ $*${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${RESET}"; }
err()  { echo -e "${RED}  ✗ $*${RESET}"; }

# ── Cleanup on exit ───────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  echo ""
  log "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null
  ok "All processes stopped."
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── 1. Docker / PostgreSQL ────────────────────────────────────────────────────
log "Starting PostgreSQL (Docker)..."
if ! docker info &>/dev/null; then
  err "Docker is not running. Please start Docker Desktop and try again."
  exit 1
fi

cd "$ROOT"
docker compose up -d --quiet-pull 2>&1 | grep -v "^$" || true

# Wait until Postgres is accepting connections (max 20s)
log "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 20); do
  if docker compose exec -T db pg_isready -U postgres &>/dev/null 2>&1; then
    ok "PostgreSQL is ready."
    break
  fi
  if [ "$i" -eq 20 ]; then
    err "PostgreSQL did not become ready in time. Check: docker compose logs db"
    exit 1
  fi
  sleep 1
done

# ── 2. Backend ────────────────────────────────────────────────────────────────
log "Starting Django backend..."
VENV="$ROOT/backend/venv"
if [ ! -f "$VENV/bin/activate" ]; then
  err "Virtualenv not found at $VENV. Run: python3 -m venv backend/venv && source backend/venv/bin/activate && pip install -r backend/requirements.txt"
  exit 1
fi

# Apply any pending migrations silently
source "$VENV/bin/activate"
cd "$ROOT/backend"
python manage.py migrate --run-syncdb 2>&1 | grep -E "(Apply|OK|Error)" || true
deactivate

# Start Django dev server and log to file
BACKEND_LOG="$ROOT/backend/backend.log"
source "$VENV/bin/activate"
(cd "$ROOT/backend" && python manage.py runserver 2>&1 | tee "$BACKEND_LOG") &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")
deactivate

# Wait for Django to be up
for i in $(seq 1 15); do
  if curl -s http://localhost:8000/api/ &>/dev/null || curl -s http://localhost:8000/admin/ &>/dev/null; then
    ok "Django backend running at http://localhost:8000"
    break
  fi
  sleep 1
done

# ── 3. Frontend ───────────────────────────────────────────────────────────────
log "Starting React frontend..."
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  warn "node_modules not found — running npm install..."
  (cd "$ROOT/frontend" && npm install)
fi

(cd "$ROOT/frontend" && npm run dev 2>&1) &
FRONTEND_PID=$!
PIDS+=("$FRONTEND_PID")

ok "React frontend starting at http://localhost:5173"

# ── Ready ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  BillClear AI is running${RESET}"
echo -e "  Frontend  → ${CYAN}http://localhost:5173${RESET}"
echo -e "  Backend   → ${CYAN}http://localhost:8000${RESET}"
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop all services"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# Keep the script alive so Ctrl+C is caught cleanly
wait
