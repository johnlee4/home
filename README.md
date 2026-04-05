# Docker Home Setup - Port Reference

Quick reference guide for all services running in your Docker home setup.

## Active Services & Ports

### 📸 Immich
- **Server**: http://localhost:2283
- **Purpose**: Photo/video management and backup
- **Status**: Up (use `docker compose -f docker/immich/docker-compose.yml ps`)

### 🎬 Jellyfin Media Stack
All services in the Jellyfin stack use centralized configs from `~/jellyfin-configs/`

#### Main Services
- **Jellyfin**: http://localhost:8096
  - Media server (movies, TV shows)
  - Config: `jellyfin-configs/jellyfin`

- **Sonarr**: http://localhost:8989
  - TV show automation
  - Config: `jellyfin-configs/sonarr`
  - Connected via: Gluetun VPN

- **Radarr**: http://localhost:7878
  - Movie automation
  - Config: `jellyfin-configs/radarr`
  - Direct connection

#### VPN & Downloads (Gluetun Network)
- **qBittorrent**: http://localhost:8080
  - Torrent client
  - Config: `jellyfin-configs/qbittorrent`
  - Connected via: Gluetun VPN

- **Prowlarr**: http://localhost:9696
  - Indexer manager
  - Config: `jellyfin-configs/prowlarr`
  - Connected via: Gluetun VPN

- **Gluetun VPN**: Internal proxy
  - Config: `jellyfin-configs/gluetun`
  - Ports exposed: 8888 (HTTP proxy), 8388 (Shadowsocks)

### 📚 Seafile File Sharing
All configs stored at: `~/[service]-data/`

- **Seafile Server**: http://localhost:8000
  - File sync & sharing
  - Config: `/opt/seafile-data`

- **Caddy (Reverse Proxy)**: 
  - HTTP: port 80
  - HTTPS: port 443

- **OnlyOffice**: http://localhost:6233
  - Office document editing integration

### 🧠 Portainer
- **Web UI**: https://localhost:9443
- **Purpose**: Docker container management
- **Data**: `~/portainer-data`

## Storage Paths

| Service | Config Location |
|---------|-----------------|
| Jellyfin | `~/jellyfin-configs/jellyfin` |
| Sonarr | `~/jellyfin-configs/sonarr` |
| Radarr | `~/jellyfin-configs/radarr` |
| qBittorrent | `~/jellyfin-configs/qbittorrent` |
| Prowlarr | `~/jellyfin-configs/prowlarr` |
| Gluetun | `~/jellyfin-configs/gluetun` |
| Portainer | `~/portainer-data` |
| Immich DB | `~/immich-data/postgres` |
| Media Library | `~/media-data` |

## Useful Scripts

- **Start all services**: `./scripts/start-all.sh`
- **Stop all services**: `./scripts/stop_all.sh`
- **Backup everything**: `./scripts/backup.sh` (creates backups in `~/backups` including Docker configs, Jellyfin configs, Portainer data, and Immich database)

## Quick Commands

```bash
# Start all services
./scripts/start-all.sh

# Stop all services
./scripts/stop_all.sh

# Check service status
docker-compose -f docker/jellyfin/docker-compose.yml ps

# View logs for a specific container
docker logs <container_name>

# Backup your configuration
./scripts/backup.sh

# Check Docker resource usage
docker system df
```

## VPN Services

The following services are routed through Gluetun VPN:
- qBittorrent (port 8080)
- Prowlarr (port 9696)

To access these services locally, you can use the exposed ports above. Configure them to reach the internet through the VPN as defined in `jellyfin-configs/gluetun`.

## Port Summary

| Port | Service |
|------|---------|
| 2283 | Immich |
| 6233 | OnlyOffice |
| 7878 | Radarr |
| 8000 | Seafile |
| 8080 | qBittorrent |
| 8089 | Sonarr |
| 8096 | Jellyfin |
| 8888 | Gluetun HTTP Proxy |
| 8388 | Gluetun Shadowsocks |
| 9443 | Portainer |
| 9696 | Prowlarr |
| 80 | Caddy (HTTP) |
| 443 | Caddy (HTTPS) |