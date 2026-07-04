#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  MOYA Agent Studio — start.sh
#  Installs dependencies and starts backend + frontend together.
#  Usage:  ./start.sh
#          ./start.sh --no-install   (skip pip / npm install)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

BACKEND_PORT=8000
FRONTEND_PORT=5173
SKIP_INSTALL=false

# ── Parse flags ───────────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --no-install) SKIP_INSTALL=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${BOLD}  MOYA Agent Studio${NC}"
  echo -e "  Visual builder for multi-agent pipelines"
  echo ""
}

ok()   { echo -e "  ${GREEN}✓${NC}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "  ${RED}✗${NC}  $*"; }
info() { echo -e "  ${BLUE}→${NC}  $*"; }

# ── Dependency checks ─────────────────────────────────────────────────────────
check_deps() {
  echo -e "${BOLD}  Checking dependencies${NC}"
  local missing=0

  if command -v python3 &>/dev/null; then
    local pyver
    pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    ok "python3 ${pyver}"
  else
    err "python3 not found — install Python 3.9+ from https://python.org"
    missing=1
  fi

  if command -v node &>/dev/null; then
    ok "node $(node --version)"
  else
    err "node not found — install Node.js 18+ from https://nodejs.org"
    missing=1
  fi

  if command -v npm &>/dev/null; then
    ok "npm $(npm --version)"
  else
    err "npm not found — install Node.js 18+ from https://nodejs.org"
    missing=1
  fi

  if [ $missing -ne 0 ]; then
    echo ""
    err "Missing required dependencies. Please install them and re-run."
    exit 1
  fi
  echo ""
}

# ── Install ───────────────────────────────────────────────────────────────────
install_deps() {
  if $SKIP_INSTALL; then
    warn "Skipping dependency install (--no-install)"
    echo ""
    return
  fi

  echo -e "${BOLD}  Installing dependencies${NC}"

  info "pip install -r backend/requirements.txt"
  pip3 install -r "$BACKEND_DIR/requirements.txt" -q \
    && ok "Backend Python packages ready" \
    || { err "pip install failed"; exit 1; }

  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    info "npm install (first run — may take a minute)"
    npm install --prefix "$FRONTEND_DIR" --silent \
      && ok "Frontend packages ready" \
      || { err "npm install failed"; exit 1; }
  else
    ok "Frontend packages already installed"
  fi

  echo ""
}

# ── Port check ────────────────────────────────────────────────────────────────
check_port() {
  local port=$1
  if lsof -ti tcp:"$port" &>/dev/null; then
    warn "Port $port already in use — attempting to free it"
    lsof -ti tcp:"$port" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

# ── Start backend ─────────────────────────────────────────────────────────────
start_backend() {
  echo -e "${BOLD}  Starting backend${NC}"
  check_port $BACKEND_PORT

  cd "$BACKEND_DIR"
  python3 main.py >"$SCRIPT_DIR/.backend.log" 2>&1 &
  BACKEND_PID=$!
  cd "$SCRIPT_DIR"

  # Wait for the health endpoint (up to 10 s)
  local waited=0
  while ! curl -s "http://localhost:${BACKEND_PORT}/health" &>/dev/null; do
    if [ $waited -ge 10 ]; then
      err "Backend did not start within 10 s"
      echo ""
      warn "Last log lines:"
      tail -20 "$SCRIPT_DIR/.backend.log" | sed 's/^/    /'
      kill $BACKEND_PID 2>/dev/null
      exit 1
    fi
    sleep 1
    waited=$((waited + 1))
  done

  ok "Backend running on http://localhost:${BACKEND_PORT} (PID ${BACKEND_PID})"
  echo ""
}

# ── Cleanup ───────────────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "  Stopping services…"
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null && ok "Backend stopped"
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null && ok "Frontend stopped"
  rm -f "$SCRIPT_DIR/.backend.log"
  echo ""
  exit 0
}
trap cleanup INT TERM

# ─────────────────────────────────────────────────────────────────────────────
banner
check_deps
install_deps
start_backend

echo -e "${BOLD}  Starting frontend${NC}"
check_port $FRONTEND_PORT

# Run Vite in the foreground so Ctrl+C kills everything via the trap
echo ""
echo -e "  ${GREEN}${BOLD}Open: http://localhost:${FRONTEND_PORT}${NC}"
echo ""
echo -e "  Backend logs: ${SCRIPT_DIR}/.backend.log"
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop both services"
echo ""

npm run dev --prefix "$FRONTEND_DIR"
