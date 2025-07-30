#!/usr/bin/env bash

set -e

# === Colors ===
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${CYAN}$1${NC}"; }
info()  { echo -e "${GREEN}$1${NC}"; }
warn()  { echo -e "${YELLOW}$1${NC}"; }

# === Usage Check ===
if [ $# -ne 2 ]; then
  echo -e "${RED}Usage: $0 <number_of_requests> <parallel_processes>${NC}"
  exit 1
fi

REQ_COUNT="$1"
PARALLEL="$2"

APP_CONTAINER="myportfolio-load"
DB_CONTAINER="mysql-load"
BASE_URL="http://localhost:3000"

LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_STATS_FILE="$LOG_DIR/stats-app_${TIMESTAMP}.log"
DB_STATS_FILE="$LOG_DIR/stats-db_${TIMESTAMP}.log"

HEADER="Timestamp,Method,CPU%,MemUsage,Mem%,NetIO,BlockIO,PIDs"
echo "$HEADER" > "$APP_STATS_FILE"
echo "$HEADER" > "$DB_STATS_FILE"

cleanup() {
  warn "Cleaning up Docker containers..."
  docker compose -f docker-compose-load-test.yml down > /dev/null 2>&1 || true
  kill "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true
  wait "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true
}
trap cleanup EXIT INT

log "Starting Docker containers..."
docker compose -f docker-compose-load-test.yml down > /dev/null 2>&1
docker compose -f docker-compose-load-test.yml up -d > /dev/null 2>&1

log "Waiting for container ${YELLOW}$APP_CONTAINER${CYAN} to start..."
until [ "$(docker inspect -f '{{.State.Running}}' "$APP_CONTAINER" 2>/dev/null)" == "true" ]; do
  sleep 1
done

log "Waiting for Flask app to be ready at ${YELLOW}$BASE_URL${CYAN}..."
until curl -s --fail "$BASE_URL/" > /dev/null; do
  sleep 1
done

log "Raising CPU priority for $APP_CONTAINER..."
docker update --cpu-shares 1024 "$APP_CONTAINER" > /dev/null 2>&1 || true

sample_interval=0.2  # 200 milliseconds

log_stats_loop() {
  local container=$1
  local outfile=$2
  local method=$3
  while true; do
    ts=$(date +%s.%3N 2>/dev/null || date +%s)
    stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}" "$container" 2>/dev/null)
    echo "$ts,$method,$stats" >> "$outfile"
    sleep "$sample_interval"
  done
}

log "Starting POST phase stats logging..."
log_stats_loop "$APP_CONTAINER" "$APP_STATS_FILE" "POST" &
APP_STATS_PID=$!
log_stats_loop "$DB_CONTAINER" "$DB_STATS_FILE" "POST" &
DB_STATS_PID=$!

start_time=$(date +%s)

log "Adding $REQ_COUNT posts with $PARALLEL parallel threads..."
seq 1 "$REQ_COUNT" | xargs -P"$PARALLEL" -I{} curl -s -H 'Content-Type: multipart/form-data' \
  -F 'name=TEST' -F 'email=TEST@TEST.COM' -F 'content=TEST' \
  "$BASE_URL/api/timeline_post?load_id={}" > /dev/null

log "POST phase completed. Stopping POST stats logging..."
kill "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true
wait "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true

log "Starting GET phase stats logging..."
log_stats_loop "$APP_CONTAINER" "$APP_STATS_FILE" "GET" &
APP_STATS_PID=$!
log_stats_loop "$DB_CONTAINER" "$DB_STATS_FILE" "GET" &
DB_STATS_PID=$!

log "Fetching $REQ_COUNT posts using $PARALLEL parallel threads..."
seq 1 "$REQ_COUNT" | xargs -P"$PARALLEL" -I{} curl -s "$BASE_URL/api/timeline_post?load_id={}" > /dev/null

log "GET phase completed. Stopping GET stats logging..."
kill "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true
wait "$APP_STATS_PID" "$DB_STATS_PID" 2>/dev/null || true

end_time=$(date +%s)
duration=$((end_time - start_time))

info "Load test completed in ${YELLOW}$duration${GREEN} seconds"
info "App stats saved to ${YELLOW}$APP_STATS_FILE${NC}"
info "DB stats saved to ${YELLOW}$DB_STATS_FILE${NC}"