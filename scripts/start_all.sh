#!/bin/bash

set -e

BASE_DIR=~/john-git/home
JELLYFIN_DIR=$BASE_DIR/docker/jellyfin
JELLYFIN_ENV=$JELLYFIN_DIR/.env

echo "🚀 Starting all services..."

# Immich
echo "📸 Starting Immich..."
docker compose -f $BASE_DIR/docker/immich/docker-compose.yml up -d

# Jellyfin
echo "🎬 Starting Jellyfin..."
if [ ! -f "$JELLYFIN_ENV" ]; then
	echo "⚠️  Missing $JELLYFIN_ENV"
	echo "   Copy .env.example first:"
	echo "   cp $JELLYFIN_DIR/.env.example $JELLYFIN_ENV"
	exit 1
fi
docker compose --env-file $JELLYFIN_ENV -f $JELLYFIN_DIR/docker-compose.yml up -d

# Portainer
echo "🧠 Starting Portainer..."
docker-compose -f $BASE_DIR/docker/portainer/docker-compose.yml up -d

# Pi-hole
echo "🛡️ Starting Pi-hole..."
docker compose -f $BASE_DIR/docker/pi-hole/docker-compose.yml up -d

# Seafile
echo "📚 Starting Seafile..."
# use the env file here build the docker-compose command with the env file
cd $BASE_DIR/docker/seafile
docker compose up -d
cd -
echo "✅ All services started"
