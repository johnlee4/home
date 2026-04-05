#!/bin/bash

set -e

BASE_DIR=~/john-git/home

echo "🚀 Starting all services..."

# Start Colima first
#bash $BASE_DIR/scripts/start-colima.sh

# Immich
echo "📸 Starting Immich..."
docker compose -f $BASE_DIR/docker/immich/docker-compose.yml up -d

# Jellyfin
echo "🎬 Starting Jellyfin..."
docker compose -f $BASE_DIR/docker/jellyfin/docker-compose.yml up -d

# Portainer
echo "🧠 Starting Portainer..."
docker-compose -f $BASE_DIR/docker/portainer/docker-compose.yml up -d

# Seafile
echo "📚 Starting Seafile..."
# use the env file here build the docker-compose command with the env file
cd $BASE_DIR/docker/seafile
docker-compose  up -d
cd -
echo "✅ All services started"
