# Docker Home Setup - Port Reference

Quick reference guide for all services running in your Docker home setup.

## Active Services & Ports

### 📸 Immich
- **Server**: http://localhost:2283
- **Purpose**: Photo/video management and backup
- **Status**: Up (use `docker compose -f docker/immich/docker-compose.yml ps`)

### 🎬 Jellyfin Media Stack
All services in the Jellyfin stack are defined in `docker/jellyfin/docker-compose.yml` and use env config from `docker/jellyfin/.env`.

#### First-Time Setup
```bash
cp docker/jellyfin/.env.example docker/jellyfin/.env
mkdir -p /Volumes/Seagate2T/media/config/{gluetun,qbittorrent,sonarr,radarr,bazarr,prowlarr,jellyfin,jellyfin-cache,seerr}
mkdir -p /Volumes/Seagate2T/media/downloads/{incomplete,complete}
mkdir -p /Volumes/Seagate2T/media/{movies,tv,subtitles}
```

Then edit `docker/jellyfin/.env` and set your Surfshark values:
- `WIREGUARD_PRIVATE_KEY`
- `WIREGUARD_ADDRESSES`
- `SERVER_COUNTRIES`

#### Main Services
- **Jellyfin**: http://localhost:8096
  - Media server (movies, TV shows)
  - Config: `/Volumes/Seagate2T/media/config/jellyfin`

- **Seerr**: http://localhost:5055
  - Request management for Jellyfin users
  - Config: `/Volumes/Seagate2T/media/config/seerr`

- **Sonarr**: http://localhost:8989
  - TV show automation
  - Config: `/Volumes/Seagate2T/media/config/sonarr`

- **Radarr**: http://localhost:7878
  - Movie automation
  - Config: `/Volumes/Seagate2T/media/config/radarr`

- **Bazarr**: http://localhost:6767
  - Subtitle automation
  - Config: `/Volumes/Seagate2T/media/config/bazarr`

#### VPN & Downloads (Gluetun Network)
- **qBittorrent**: http://localhost:8080
  - Torrent client
  - Config: `/Volumes/Seagate2T/media/config/qbittorrent`
  - Connected via: Gluetun VPN

- **Prowlarr**: http://localhost:9696
  - Indexer manager
  - Config: `/Volumes/Seagate2T/media/config/prowlarr`
  - Runs on local network (not routed through VPN)

- **Gluetun VPN**: Internal proxy
  - Config: `/Volumes/Seagate2T/media/config/gluetun`
  - VPN provider: Surfshark
  - qBittorrent is the only service routed through VPN

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

### 🛡️ Pi-hole
- **Admin UI**: http://localhost:8081/admin
- **Purpose**: Network-wide ad blocking and DNS filtering
- **DNS Ports**: 53/tcp, 53/udp

## Storage Paths

| Service | Config Location |
|---------|-----------------|
| Jellyfin | `/Volumes/Seagate2T/media/config/jellyfin` |
| Sonarr | `/Volumes/Seagate2T/media/config/sonarr` |
| Radarr | `/Volumes/Seagate2T/media/config/radarr` |
| Bazarr | `/Volumes/Seagate2T/media/config/bazarr` |
| qBittorrent | `/Volumes/Seagate2T/media/config/qbittorrent` |
| Prowlarr | `/Volumes/Seagate2T/media/config/prowlarr` |
| Gluetun | `/Volumes/Seagate2T/media/config/gluetun` |
| Seerr | `/Volumes/Seagate2T/media/config/seerr` |
| Portainer | `~/portainer-data` |
| Immich DB | `~/immich-data/postgres` |
| Media Library | `/Volumes/Seagate2T/media` |

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
docker compose --env-file docker/jellyfin/.env -f docker/jellyfin/docker-compose.yml ps
docker compose -f docker/pi-hole/docker-compose.yml ps

# View logs for a specific container
docker logs <container_name>

# Backup your configuration
./scripts/backup.sh

# Hard reset the media stack (no backup)
FORCE_RESET=true ./scripts/reset_jellyfin_stack.sh

# Check Docker resource usage
docker system df
```

## Restart Playbook

Use these commands from the repo root:

```bash
cd /Users/gayee/john-git/home
```

Restart all home services:

```bash
./scripts/stop_all.sh && ./scripts/start-all.sh
```

Restart only the Jellyfin media stack:

```bash
docker compose --env-file docker/jellyfin/.env -f docker/jellyfin/docker-compose.yml down
docker compose --env-file docker/jellyfin/.env -f docker/jellyfin/docker-compose.yml up -d
```

If qBittorrent WebUI is unreachable, force recreate Gluetun + qBittorrent together:

```bash
docker compose --env-file docker/jellyfin/.env -f docker/jellyfin/docker-compose.yml up -d --force-recreate gluetun qbittorrent
```

Confirm status after restart:

```bash
docker compose --env-file docker/jellyfin/.env -f docker/jellyfin/docker-compose.yml ps
```

## Automated qBittorrent Cleanup (Cron)

Use this when you want torrents removed from qBittorrent only after Sonarr/Radarr has imported them into your Movies/TV library.

1. Copy the environment template and fill your values:

```bash
cp ./scripts/qbit_cleanup.env.example ./scripts/.env
```

2. Edit `./scripts/.env`:
  - Set `QBIT_USERNAME` and `QBIT_PASSWORD`
  - Set `SONARR_API_KEY` and/or `RADARR_API_KEY`
  - Keep `DRY_RUN=true` for first test

3. Run a manual test:

```bash
python3 ./scripts/qbit_cleanup_imported.py
```

4. If output looks correct, set `DRY_RUN=false` in `./scripts/.env`.

5. Add cron (every 360 minutes):

```bash
crontab -e
```

Add this line:

```cron
*/360 * * * * cd /Users/gayee/john-git/home && ./scripts/qbit_cleanup_runner.sh
```

6. Check job output:

```bash
tail -f ./scripts/qbit_cleanup.log
```

7. Optional log rotation tuning (defaults: 10 MB, keep 5 files):
  - `QBIT_CLEANUP_LOG_MAX_MB`
  - `QBIT_CLEANUP_LOG_MAX_FILES`

## VPN Services

The following service is routed through Gluetun VPN (Surfshark):
- qBittorrent (port 8080)

The following services stay on local networking:
- Jellyfin (port 8096)
- Seerr (port 5055)
- Sonarr (port 8989)
- Radarr (port 7878)
- Bazarr (port 6767)
- Prowlarr (port 9696)

To access these services locally, use the exposed ports above. qBittorrent traffic is routed through the VPN as defined in `/Volumes/Seagate2T/media/config/gluetun`.

## Gluetun Pytest Checks

Run non-destructive VPN checks:

```bash
cd /Users/gayee/john-git/home
python3 -m pytest -q tests/test_gluetun_network.py -m "not destructive"
```

Run full checks including kill-switch behavior (will briefly stop Gluetun):

```bash
cd /Users/gayee/john-git/home
RUN_DESTRUCTIVE_GLUETUN_TESTS=1 python3 -m pytest -q tests/test_gluetun_network.py
```

## Port Summary

| Port | Service |
|------|---------|
| 2283 | Immich |
| 5055 | Seerr |
| 6233 | OnlyOffice |
| 7878 | Radarr |
| 6767 | Bazarr |
| 8000 | Seafile |
| 8080 | qBittorrent |
| 8081 | Pi-hole Admin UI |
| 8989 | Sonarr |
| 8096 | Jellyfin |
| 9443 | Portainer |
| 9696 | Prowlarr |
| 53/tcp | Pi-hole DNS |
| 53/udp | Pi-hole DNS |
| 80 | Caddy (HTTP) |
| 443 | Caddy (HTTPS) |