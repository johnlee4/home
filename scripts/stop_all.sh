#!/bin/bash

set -e

BASE_DIR=~/john-git/home
JELLYFIN_DIR=$BASE_DIR/docker/jellyfin
JELLYFIN_ENV=$JELLYFIN_DIR/.env

echo "🛑 Stopping all services..."

# Stop Seafile first (reverse order of start)
echo "📚 Stopping Seafile..."
cd $BASE_DIR/docker/seafile
docker compose down
cd -

# Stop Pi-hole
echo "🛡️ Stopping Pi-hole..."
docker compose -f $BASE_DIR/docker/pi-hole/docker-compose.yml down

# Stop Portainer
echo "🧠 Stopping Portainer..."
docker compose -f $BASE_DIR/docker/portainer/docker-compose.yml down

# Stop Jellyfin
echo "🎬 Stopping Jellyfin..."
if [ -f "$JELLYFIN_ENV" ]; then
	docker compose --env-file $JELLYFIN_ENV -f $JELLYFIN_DIR/docker-compose.yml down
else
	docker compose -f $JELLYFIN_DIR/docker-compose.yml down || true
fi

# Stop Immich
echo "📸 Stopping Immich..."
docker compose -f $BASE_DIR/docker/immich/docker-compose.yml down


echo "✅ All services stopped"