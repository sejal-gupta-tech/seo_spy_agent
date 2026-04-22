#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

FRONTEND_DIR="frontend"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
FRONTEND_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}/"
FRONTEND_READY_MARKER="${FRONTEND_READY_MARKER:-SEO Spy Studio}"
FRONTEND_START_TIMEOUT="${FRONTEND_START_TIMEOUT:-45}"
FRONTEND_LOG_FILE="$(mktemp "${TMPDIR:-/tmp}/seo-spy-frontend.XXXXXX")"
FRONTEND_PID=""
FRONTEND_STARTED_BY_SCRIPT=0

should_start_frontend() {
  for arg in "$@"; do
    if [[ "$arg" == "--check-only" ]]; then
      return 1
    fi
  done

  return 0
}

stop_frontend_process() {
  if [[ "$FRONTEND_STARTED_BY_SCRIPT" -eq 1 && -n "$FRONTEND_PID" ]]; then
    echo "Stopping frontend..."
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi

  FRONTEND_PID=""
  FRONTEND_STARTED_BY_SCRIPT=0
}

cleanup() {
  local exit_code=$?
  stop_frontend_process
  rm -f "$FRONTEND_LOG_FILE"
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

print_frontend_logs() {
  echo "Frontend failed to start cleanly. Last log lines:" >&2
  tail -n 80 "$FRONTEND_LOG_FILE" >&2 || true
}

frontend_healthcheck() {
  local body_file
  body_file="$(mktemp "${TMPDIR:-/tmp}/seo-spy-frontend-body.XXXXXX")"

  local status_code="000"
  if status_code="$(
    curl -sS --max-time 2 \
      -o "$body_file" \
      -w "%{http_code}" \
      "$FRONTEND_URL" 2>/dev/null
  )"; then
    if [[ "$status_code" == "200" ]] && grep -q "$FRONTEND_READY_MARKER" "$body_file"; then
      rm -f "$body_file"
      return 0
    fi
  fi

  rm -f "$body_file"
  return 1
}

wait_for_frontend() {
  local deadline=$((SECONDS + FRONTEND_START_TIMEOUT))

  while (( SECONDS < deadline )); do
    if frontend_healthcheck; then
      echo "Frontend ready at $FRONTEND_URL"
      echo "Frontend logs: $FRONTEND_LOG_FILE"
      return 0
    fi

    if [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
      return 1
    fi

    sleep 1
  done

  return 1
}

ensure_frontend_dependencies() {
  if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
    echo "Installing frontend dependencies..."
    (
      cd "$FRONTEND_DIR"
      npm install
    )
  else
    echo "Using existing frontend dependencies."
  fi
}

start_frontend_process() {
  : > "$FRONTEND_LOG_FILE"

  (
    cd "$FRONTEND_DIR"
    npm run dev -- --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
  ) >"$FRONTEND_LOG_FILE" 2>&1 &

  FRONTEND_PID=$!
  FRONTEND_STARTED_BY_SCRIPT=1
}

start_frontend() {
  if frontend_healthcheck; then
    echo "Using existing frontend at $FRONTEND_URL"
    echo "Skipping new frontend startup because the current instance is healthy."
    return 0
  fi

  ensure_frontend_dependencies

  local cleaned_cache=0

  while true; do
    echo "Starting frontend..."
    start_frontend_process

    if wait_for_frontend; then
      return 0
    fi

    stop_frontend_process

    if [[ "$cleaned_cache" -eq 0 && -d "${FRONTEND_DIR}/.next" ]]; then
      echo "Frontend health check failed. Clearing ${FRONTEND_DIR}/.next and retrying once..."
      rm -rf "${FRONTEND_DIR}/.next"
      cleaned_cache=1
      continue
    fi

    print_frontend_logs
    exit 1
  done
}

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required to verify the frontend health check." >&2
  exit 1
fi

if should_start_frontend "$@"; then
  start_frontend
else
  echo "Skipping frontend startup in check-only mode."
fi

echo "Starting backend..."
if command -v python3 >/dev/null 2>&1; then
  python3 run_project.py "$@"
elif command -v python >/dev/null 2>&1; then
  python run_project.py "$@"
else
  echo "Python 3 is required but was not found in PATH." >&2
  exit 1
fi
