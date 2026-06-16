#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ViralFlux — Health Check Script
#
# Checks whether all Docker services are running and key HTTP endpoints
# are responding correctly.
#
# Usage:
#   bash scripts/health_check.sh
#
# Exit codes:
#   0 — All checks passed
#   1 — One or more checks failed
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL="${VIRALFLUX_URL:-http://localhost}"
COMPOSE_CMD="docker compose"
TIMEOUT=10  # seconds per HTTP request

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Helpers ──────────────────────────────────────────────────────────────────

pass() {
  echo -e "  ${GREEN}[PASS]${RESET}  $1"
}

fail() {
  echo -e "  ${RED}[FAIL]${RESET}  $1"
  FAILURES=$((FAILURES + 1))
}

warn() {
  echo -e "  ${YELLOW}[WARN]${RESET}  $1"
}

section() {
  echo ""
  echo -e "${BOLD}${CYAN}$1${RESET}"
  echo -e "${CYAN}$(printf '─%.0s' $(seq 1 50))${RESET}"
}

FAILURES=0

# ─── 1. Docker Compose Service Status ────────────────────────────────────────

section "1. Docker Compose Service Status"

echo ""
${COMPOSE_CMD} ps 2>&1 || true
echo ""

# Expected services
EXPECTED_SERVICES=("postgres" "redis" "backend" "worker" "beat" "frontend" "n8n" "nginx")

for service in "${EXPECTED_SERVICES[@]}"; do
  status=$(${COMPOSE_CMD} ps --status running --format "{{.Name}}" 2>/dev/null | grep -w "^${service}$" || echo "")
  if [[ -n "${status}" ]]; then
    pass "Service '${service}' is running"
  else
    fail "Service '${service}' is NOT running (or not found)"
  fi
done

# ─── 2. Docker Health Checks ─────────────────────────────────────────────────

section "2. Docker Health Check Status"

echo ""
# Check postgres and redis which have explicit healthchecks defined
for service in "postgres" "redis"; do
  health=$(${COMPOSE_CMD} ps --format "{{.Name}} {{.Health}}" 2>/dev/null | grep "^${service} " | awk '{print $2}' || echo "unknown")
  case "${health}" in
    healthy)
      pass "Service '${service}' health: healthy"
      ;;
    starting)
      warn "Service '${service}' health: starting (give it a moment)"
      ;;
    unhealthy)
      fail "Service '${service}' health: UNHEALTHY"
      ;;
    *)
      warn "Service '${service}' health: ${health:-unknown} (no healthcheck configured or status unavailable)"
      ;;
  esac
done

# ─── 3. HTTP Endpoint Checks ─────────────────────────────────────────────────

section "3. HTTP Endpoint Checks"

check_http() {
  local label="$1"
  local url="$2"
  local expected_min="$3"   # minimum acceptable HTTP status code
  local expected_max="$4"   # maximum acceptable HTTP status code
  local description="$5"

  local http_status
  http_status=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "${TIMEOUT}" \
    --connect-timeout 5 \
    "${url}" 2>/dev/null || echo "000")

  if [[ "${http_status}" -ge "${expected_min}" && "${http_status}" -le "${expected_max}" ]]; then
    pass "${label} → HTTP ${http_status}  (${description})"
  elif [[ "${http_status}" == "000" ]]; then
    fail "${label} → Connection refused or timed out  [URL: ${url}]"
  else
    fail "${label} → HTTP ${http_status}  (expected ${expected_min}–${expected_max})  [URL: ${url}]"
  fi
}

echo ""

# Frontend — Next.js should return 200
check_http "Frontend" \
  "${BASE_URL}/" \
  200 200 \
  "Next.js landing page"

# FastAPI health endpoint — should return 200
check_http "API health" \
  "${BASE_URL}/api/health" \
  200 200 \
  "FastAPI /health endpoint"

# FastAPI root — returns 404 (no route at /api/v1 root) or 200 with API info
check_http "API v1 root" \
  "${BASE_URL}/api/v1" \
  200 404 \
  "Returns 404 (no root route) or 200 if root route is defined"

# FastAPI Swagger docs
check_http "API Swagger UI" \
  "${BASE_URL}/api/docs" \
  200 200 \
  "FastAPI interactive documentation"

# n8n — should return 200 (login page) after authentication or redirect
check_http "n8n workflow UI" \
  "${BASE_URL}/n8n/" \
  200 401 \
  "n8n UI (200=loaded, 401=auth required)"

# Auth register endpoint — returns 422 on empty POST (validation), which means the route exists
check_http "API register route" \
  "${BASE_URL}/api/v1/auth/register" \
  405 422 \
  "POST-only route; GET returns 405 Method Not Allowed"

# ─── 4. Direct Container Port Checks (internal) ──────────────────────────────

section "4. Internal Container Port Checks"

echo ""

# Check backend directly (bypassing Nginx) if accessible
check_http "Backend direct (port 8000)" \
  "http://localhost:8000/api/health" \
  200 200 \
  "FastAPI direct — bypasses Nginx"

# ─── 5. Summary ───────────────────────────────────────────────────────────────

section "Summary"
echo ""

if [[ "${FAILURES}" -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}All checks passed.${RESET} ViralFlux is healthy."
  echo ""
  echo -e "  Frontend:   ${BASE_URL}"
  echo -e "  API docs:   ${BASE_URL}/api/docs"
  echo -e "  n8n UI:     ${BASE_URL}/n8n"
  echo ""
  exit 0
else
  echo -e "${RED}${BOLD}${FAILURES} check(s) failed.${RESET}"
  echo ""
  echo "Troubleshooting tips:"
  echo "  1. Run 'make ps' to see all container statuses"
  echo "  2. Run 'make logs' to follow all service logs"
  echo "  3. Run 'docker compose logs backend' for backend-specific errors"
  echo "  4. Check your .env file for missing or incorrect values"
  echo "  5. Ensure ports 80 and 8000 are not blocked by a firewall"
  echo ""
  exit 1
fi
