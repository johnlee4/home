#!/bin/bash

set -e

BASE_DIR=~/john-git/home

echo "🛑 Stopping all services..."

# Stop Seafile first (reverse order of start)
echo "📚 Stopping Seafile..."
cd $BASE_DIR/docker/seafile
docker-compose down
cd -

# Stop Portainer
echo "🧠 Stopping Portainer..."
docker-compose -f $BASE_DIR/docker/portainer/docker-compose.yml down

# Stop Jellyfin
echo "🎬 Stopping Jellyfin..."
docker compose -f $BASE_DIR/docker/jellyfin/docker-compose.yml down

# Stop Immich
echo "📸 Stopping Immich..."
docker compose -f $BASE_DIR/docker/immich/docker-compose.yml down


echo "✅ All services stopped"