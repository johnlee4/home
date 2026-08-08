#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$ROOT_DIR/scripts/qbit_cleanup.log"
MAX_MB="${QBIT_CLEANUP_LOG_MAX_MB:-10}"
MAX_FILES="${QBIT_CLEANUP_LOG_MAX_FILES:-5}"

rotate_log() {
  local max_bytes current_size i
  max_bytes=$((MAX_MB * 1024 * 1024))

  [[ -f "$LOG_FILE" ]] || return 0

  current_size=$(wc -c < "$LOG_FILE" | tr -d ' ')
  if (( current_size < max_bytes )); then
    return 0
  fi

  i=$MAX_FILES
  while (( i >= 1 )); do
    if (( i == MAX_FILES )); then
      rm -f "$LOG_FILE.$i"
    fi
    if [[ -f "$LOG_FILE.$((i - 1))" ]]; then
      mv "$LOG_FILE.$((i - 1))" "$LOG_FILE.$i"
    fi
    i=$((i - 1))
  done

  mv "$LOG_FILE" "$LOG_FILE.1"
}

rotate_log

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting qBittorrent cleanup" >> "$LOG_FILE"
/usr/bin/env python3 "$ROOT_DIR/scripts/qbit_cleanup_imported.py" >> "$LOG_FILE" 2>&1
rc=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished qBittorrent cleanup (exit=$rc)" >> "$LOG_FILE"
exit "$rc"
