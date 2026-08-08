from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT_DIR / "docker/jellyfin/docker-compose.yml"
ENV_FILE = ROOT_DIR / "docker/jellyfin/.env"
GLUETUN_CONTAINER = "media_gluetun"
QBIT_CONTAINER = "media_qbittorrent"


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _compose_available() -> bool:
    if not _docker_available():
        return False
    result = _run(["docker", "compose", "version"], check=False)
    return result.returncode == 0


def _container_running(name: str) -> bool:
    result = _run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def _public_ip_from_host() -> str:
    with urllib.request.urlopen("https://ipinfo.io/ip", timeout=10) as resp:
        return resp.read().decode("utf-8").strip()


def _public_ip_from_container(container_name: str) -> str:
    result = _run(
        [
            "docker",
            "exec",
            container_name,
            "sh",
            "-c",
            "wget -qO- https://ipinfo.io/ip || curl -fsSL https://ipinfo.io/ip",
        ]
    )
    return result.stdout.strip()


def _assert_runtime_prereqs() -> None:
    if not COMPOSE_FILE.exists():
        pytest.skip(f"Missing compose file: {COMPOSE_FILE}")
    if not ENV_FILE.exists():
        pytest.skip(f"Missing env file: {ENV_FILE}")
    if not _compose_available():
        pytest.skip("docker compose is not available")


@pytest.fixture(scope="module")
def runtime_prereqs() -> None:
    _assert_runtime_prereqs()


def test_compose_routes_qbittorrent_through_gluetun() -> None:
    content = COMPOSE_FILE.read_text(encoding="utf-8")
    assert "network_mode: service:gluetun" in content


def test_compose_config_resolves(runtime_prereqs: None) -> None:
    result = _run(
        [
            "docker",
            "compose",
            "--env-file",
            str(ENV_FILE),
            "-f",
            str(COMPOSE_FILE),
            "config",
        ],
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_gluetun_logs_public_ip(runtime_prereqs: None) -> None:
    if not _container_running(GLUETUN_CONTAINER):
        pytest.skip("media_gluetun is not running")

    result = _run(["docker", "logs", "--tail=300", GLUETUN_CONTAINER], check=False)
    assert result.returncode == 0
    assert "Public IP address is" in result.stderr or "Public IP address is" in result.stdout


def test_gluetun_egress_ip_differs_from_host(runtime_prereqs: None) -> None:
    if not _container_running(GLUETUN_CONTAINER):
        pytest.skip("media_gluetun is not running")

    host_ip = _public_ip_from_host()
    container_ip = _public_ip_from_container(GLUETUN_CONTAINER)
    assert host_ip
    assert container_ip
    assert host_ip != container_ip


def test_qbittorrent_uses_gluetun_namespace(runtime_prereqs: None) -> None:
    if not _container_running(QBIT_CONTAINER):
        pytest.skip("media_qbittorrent is not running")

    result = _run(
        ["docker", "inspect", "-f", "{{.HostConfig.NetworkMode}}", QBIT_CONTAINER],
        check=False,
    )
    assert result.returncode == 0
    mode = result.stdout.strip()
    assert "gluetun" in mode or mode.startswith("container:")


@pytest.mark.destructive
def test_killswitch_blocks_qbittorrent_traffic(runtime_prereqs: None) -> None:
    if os.getenv("RUN_DESTRUCTIVE_GLUETUN_TESTS", "0") != "1":
        pytest.skip("Set RUN_DESTRUCTIVE_GLUETUN_TESTS=1 to run kill-switch test")

    if not _container_running(GLUETUN_CONTAINER):
        pytest.skip("media_gluetun is not running")
    if not _container_running(QBIT_CONTAINER):
        pytest.skip("media_qbittorrent is not running")

    try:
        stop = _run(["docker", "stop", GLUETUN_CONTAINER], check=False)
        assert stop.returncode == 0, stop.stderr

        blocked = _run(
            [
                "docker",
                "exec",
                QBIT_CONTAINER,
                "sh",
                "-c",
                "wget -T 8 -qO- https://ipinfo.io/ip || curl -m 8 -fsSL https://ipinfo.io/ip",
            ],
            check=False,
        )
        assert blocked.returncode != 0
    finally:
        _run(["docker", "start", GLUETUN_CONTAINER], check=False)
