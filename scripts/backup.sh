#!/bin/bash

# Backup script for Docker home setup
# This script backs up Docker configurations, service configs, and data directories

set -e

# Configuration
BACKUP_DIR="/Users/gayee/backups"
DOCKER_DIR="/Users/gayee/john-git/home/docker"
JELLYFIN_CONFIGS="/Users/gayee/jellyfin-configs"
PORTAINER_DATA="/Users/gayee/portainer-data"
MEDIA_DATA="/Users/gayee/media-data"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting backup at $TIMESTAMP"

# Backup Docker compose files and configurations
echo "Backing up Docker configurations..."
tar -czf "$BACKUP_DIR/docker_configs_$TIMESTAMP.tar.gz" -C "$DOCKER_DIR/.." docker/

# Backup Jellyfin service configurations
echo "Backing up Jellyfin configurations..."
if [ -d "$JELLYFIN_CONFIGS" ]; then
    tar -czf "$BACKUP_DIR/jellyfin_configs_$TIMESTAMP.tar.gz" -C /Users/gayee jellyfin-configs/
else
    echo "Warning: Jellyfin configs directory not found at $JELLYFIN_CONFIGS"
fi

# Backup Portainer data
echo "Backing up Portainer data..."
if [ -d "$PORTAINER_DATA" ]; then
    tar -czf "$BACKUP_DIR/portainer_data_$TIMESTAMP.tar.gz" -C /Users/gayee portainer-data/
else
    echo "Warning: Portainer data directory not found at $PORTAINER_DATA"
fi

# Optional: Backup media data (commented out by default as it may be very large)
# echo "Backing up media data..."
# tar -czf "$BACKUP_DIR/media_data_$TIMESTAMP.tar.gz" -C /Users/gayee media-data/

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed successfully!"
echo "Backup files created in $BACKUP_DIR:"
ls -la "$BACKUP_DIR"/*.tar.gz