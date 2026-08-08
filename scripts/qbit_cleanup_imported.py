#!/usr/bin/env python3
"""Remove completed qBittorrent torrents only after Sonarr/Radarr imported them.

The script cross-checks qBittorrent completed torrents by info hash against
Sonarr/Radarr history downloadId values, then deletes matching torrents from
qBittorrent with data files.
"""


from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


IMPORT_EVENTS = {
    "downloadFolderImported",
    "downloadImported",
}


@dataclass
class Settings:
    qbit_url: str
    qbit_username: str
    qbit_password: str
    sonarr_url: str | None
    sonarr_api_key: str | None
    radarr_url: str | None
    radarr_api_key: str | None
    min_seed_minutes: int
    history_days: int
    dry_run: bool


def load_env_file(path: str | None) -> None:
    if not path:
        return
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        value = os.path.expandvars(value)
        os.environ.setdefault(key, value)


def env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def sanitize_api_key(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered.startswith("your-") or "change-me" in lowered:
        return None
    return value


def get_settings() -> Settings:
    env_path = os.getenv("QBIT_CLEANUP_ENV", "")
    if env_path:
        load_env_file(env_path)
    else:
        default_env = Path(__file__).with_name(".env")
        if default_env.exists():
            load_env_file(str(default_env))

    qbit_url = os.getenv("QBIT_URL", "http://localhost:8080").rstrip("/")
    qbit_username = os.getenv("QBIT_USERNAME", "")
    qbit_password = os.getenv("QBIT_PASSWORD", "")

    if not qbit_username or not qbit_password:
        raise ValueError("QBIT_USERNAME and QBIT_PASSWORD are required")

    sonarr_url = os.getenv("SONARR_URL", "").rstrip("/") or None
    sonarr_api_key = sanitize_api_key(os.getenv("SONARR_API_KEY", ""))
    radarr_url = os.getenv("RADARR_URL", "").rstrip("/") or None
    radarr_api_key = sanitize_api_key(os.getenv("RADARR_API_KEY", ""))

    if not ((sonarr_url and sonarr_api_key) or (radarr_url and radarr_api_key)):
        raise ValueError("Configure Sonarr and/or Radarr URL + API key")

    return Settings(
        qbit_url=qbit_url,
        qbit_username=qbit_username,
        qbit_password=qbit_password,
        sonarr_url=sonarr_url,
        sonarr_api_key=sonarr_api_key,
        radarr_url=radarr_url,
        radarr_api_key=radarr_api_key,
        min_seed_minutes=int(os.getenv("MIN_SEED_MINUTES", "30")),
        history_days=int(os.getenv("HISTORY_DAYS", "21")),
        dry_run=env_bool("DRY_RUN", True),
    )


class QbitClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        self._login(username, password)

    def _post(self, path: str, data: dict[str, str]) -> str:
        payload = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}{path}", data=payload, method="POST")
        with self.opener.open(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")

    def _get_json(self, path: str, params: dict[str, str] | None = None) -> list[dict]:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{self.base_url}{path}{query}", method="GET")
        with self.opener.open(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _login(self, username: str, password: str) -> None:
        body = self._post("/api/v2/auth/login", {"username": username, "password": password})
        if "Ok." not in body:
            raise RuntimeError("Failed to authenticate to qBittorrent")

    def completed_torrents(self) -> list[dict]:
        return self._get_json("/api/v2/torrents/info", {"filter": "completed"})

    def delete_torrents(self, hashes: list[str], delete_files: bool = True) -> None:
        if not hashes:
            return
        joined = "|".join(hashes)
        self._post(
            "/api/v2/torrents/delete",
            {"hashes": joined, "deleteFiles": "true" if delete_files else "false"},
        )


def arr_imported_hashes(base_url: str, api_key: str, history_days: int) -> set[str]:
    cutoff = int(time.time()) - (history_days * 86400)
    page = 1
    page_size = 1000
    imported: set[str] = set()

    while True:
        params = {
            "page": str(page),
            "pageSize": str(page_size),
            "sortDirection": "descending",
            "sortKey": "date",
        }
        url = f"{base_url}/api/v3/history?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, method="GET", headers={"X-Api-Key": api_key})

        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        records = payload.get("records", [])
        if not records:
            break

        stop_paging = False
        for rec in records:
            download_id = (rec.get("data") or {}).get("downloadId", "").lower()
            event_type = rec.get("eventType", "")

            # Guard by event type and presence of download ID first.
            if event_type in IMPORT_EVENTS and download_id:
                imported.add(download_id)

            # If record is old enough and pages are descending, stop after page.
            # Use the record date when available, otherwise continue scanning.
            date_str = rec.get("date")
            if isinstance(date_str, str):
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts = int(dt.timestamp())
                    if ts < cutoff:
                        stop_paging = True
                except ValueError:
                    pass

        total_pages = payload.get("totalPages", page)
        if stop_paging or page >= total_pages:
            break
        page += 1

    return imported


def main() -> int:
    try:
        settings = get_settings()
        qbit = QbitClient(settings.qbit_url, settings.qbit_username, settings.qbit_password)

        imported_hashes: set[str] = set()
        if settings.sonarr_url and settings.sonarr_api_key:
            imported_hashes |= arr_imported_hashes(settings.sonarr_url, settings.sonarr_api_key, settings.history_days)
        if settings.radarr_url and settings.radarr_api_key:
            imported_hashes |= arr_imported_hashes(settings.radarr_url, settings.radarr_api_key, settings.history_days)

        if not imported_hashes:
            print("No imported download IDs found in Sonarr/Radarr history. Nothing to do.")
            return 0

        now = int(time.time())
        min_seed_seconds = settings.min_seed_minutes * 60
        completed = qbit.completed_torrents()

        candidates: list[tuple[str, str]] = []
        for tor in completed:
            h = (tor.get("hash") or "").lower()
            name = tor.get("name") or h
            completion_on = int(tor.get("completion_on") or 0)
            if not h or h not in imported_hashes:
                continue
            if completion_on > 0 and (now - completion_on) < min_seed_seconds:
                continue
            candidates.append((h, name))

        if not candidates:
            print("No completed imported torrents matched deletion criteria.")
            return 0

        hashes = [h for h, _ in candidates]
        print(f"Matched {len(hashes)} torrents imported by Sonarr/Radarr.")
        for _, name in candidates:
            print(f" - {name}")

        if settings.dry_run:
            print("DRY_RUN=true, skipping deletion.")
            return 0

        qbit.delete_torrents(hashes, delete_files=True)
        print(f"Deleted {len(hashes)} torrents with files from qBittorrent.")
        return 0

    except urllib.error.HTTPError as err:
        print(f"HTTP error: {err.code} {err.reason}", file=sys.stderr)
        return 2
    except Exception as err:  # noqa: BLE001
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
