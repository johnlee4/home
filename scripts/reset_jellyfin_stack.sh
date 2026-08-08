#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JELLYFIN_DIR="$BASE_DIR/docker/jellyfin"
ENV_FILE="$JELLYFIN_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  echo "Create it first: cp $JELLYFIN_DIR/.env.example $ENV_FILE"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

: "${CONFIG_ROOT:?CONFIG_ROOT is required in $ENV_FILE}"
: "${DOWNLOADS_ROOT:?DOWNLOADS_ROOT is required in $ENV_FILE}"
: "${LIBRARY_ROOT:?LIBRARY_ROOT is required in $ENV_FILE}"

if [[ "${FORCE_RESET:-false}" != "true" ]]; then
  echo "This will remove Jellyfin stack containers, volumes, and config data."
  echo "It will keep your media library by default."
  echo "Re-run with FORCE_RESET=true to continue."
  exit 1
fi

echo "Stopping and removing Jellyfin stack..."
docker compose --env-file "$ENV_FILE" -f "$JELLYFIN_DIR/docker-compose.yml" down -v --remove-orphans

echo "Removing service config directories..."
rm -rf \
  "$CONFIG_ROOT/gluetun" \
  "$CONFIG_ROOT/qbittorrent" \
  "$CONFIG_ROOT/sonarr" \
  "$CONFIG_ROOT/radarr" \
  "$CONFIG_ROOT/bazarr" \
  "$CONFIG_ROOT/prowlarr" \
  "$CONFIG_ROOT/jellyfin" \
  "$CONFIG_ROOT/jellyfin-cache"

if [[ "${WIPE_DOWNLOADS:-false}" == "true" ]]; then
  echo "Removing downloads folder..."
  rm -rf "$DOWNLOADS_ROOT"
fi

if [[ "${WIPE_LIBRARY:-false}" == "true" ]]; then
  echo "Removing media library folder..."
  rm -rf "$LIBRARY_ROOT"
fi

echo "Jellyfin stack reset complete."
