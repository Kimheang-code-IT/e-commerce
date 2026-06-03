#!/usr/bin/env python3
"""
Auto-detect LAN IPv4 and start Docker (no manual IP in config files).

  python scripts/deploy_lan.py          # detect IP + docker compose up -d
  python scripts/deploy_lan.py --build  # also rebuild images
  python scripts/deploy_lan.py --watch  # keep printing URL if DHCP changes IP

Or double-click / run: start-lan.ps1

Public HTTPS and the SPA are served by **host nginx** (ports 80/443), not Docker.
After compose is up, proxy http://127.0.0.1:8000 — see host-nginx-examples/
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def detect_lan_ipv4() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith(("192.168.", "10.")) or ip.startswith("172."):
                second = int(ip.split(".")[1])
                if ip.startswith("172.") and not (16 <= second <= 31):
                    continue
                return ip
    except OSError:
        pass
    return None


def _read_backend_replicas() -> int:
    """BACKEND_REPLICAS from root .env (default 1)."""
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BACKEND_REPLICAS="):
                try:
                    return max(1, int(line.split("=", 1)[1].strip()))
                except ValueError:
                    break
    return 1


def detect_compose_project_name() -> str:
    """Reuse the original project name so existing volumes/containers (ecom-postgres) attach."""
    try:
        owner = subprocess.run(
            [
                "docker",
                "inspect",
                "ecom-postgres",
                "--format",
                "{{ index .Config.Labels \"com.docker.compose.project\" }}",
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if owner:
            return owner
    except OSError:
        pass

    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("COMPOSE_PROJECT_NAME=") and not line.endswith("="):
                name = line.split("=", 1)[1].strip()
                if name:
                    return name
    try:
        out = subprocess.run(
            ["docker", "volume", "ls", "-q"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    except OSError:
        out = ""
    if "e-comerce_pg_data" in out:
        return "e-comerce"
    if "e-commerce_pg_data" in out:
        return "e-commerce"
    return "e-comerce"


def write_compose_env(*, host_ip: str, backend_replicas: int) -> str:
    project = detect_compose_project_name()
    lines = [
        "# Auto-generated — do not edit; regenerated on each start (scripts/deploy_lan.py).",
        f"# Docker volume prefix: {project}_pg_data",
        f"COMPOSE_PROJECT_NAME={project}",
        f"HOST_LAN_IP={host_ip}",
        f"BACKEND_REPLICAS={backend_replicas}",
        "CORS_ALLOW_LAN=true",
        "NUXT_PUBLIC_SITE_URL=",
        "NUXT_PUBLIC_API_BASE=/api/v1",
        "NUXT_PUBLIC_USE_BACKEND_API=true",
        "FILE_BASE_URL=",
        "",
        f"# API (Docker): http://127.0.0.1:8000",
        f"# Wi-Fi (via your host nginx on 80/443): http://{host_ip}/ or https://domank-dontrey.in/",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"http://{host_ip}/"


COMPOSE_BUILD_SERVICES = [
    "backend",
    "celery-worker",
    "celery-beat",
    "telegram-bot",
]


def run_env_check() -> int:
    script = ROOT / "Backend" / "scripts" / "check_env_docker.py"
    if not script.is_file():
        return 0
    print("Checking Backend/.env for Docker...")
    return subprocess.run([sys.executable, str(script)], cwd=ROOT).returncode


def compose_up(*, build: bool, profile_beat: bool = False, backend_replicas: int = 1) -> int:
    if run_env_check() != 0:
        return 1
    compose_project = detect_compose_project_name()
    run_env = dict(**os.environ)
    run_env["COMPOSE_PROJECT_NAME"] = compose_project
    if build:
        print("Building:", ", ".join(COMPOSE_BUILD_SERVICES))
        code = subprocess.run(
            ["docker", "compose", "build", *COMPOSE_BUILD_SERVICES],
            cwd=ROOT,
            env=run_env,
        ).returncode
        if code != 0:
            return code
    cmd = ["docker", "compose", "up", "-d", "--scale", f"backend={backend_replicas}"]
    if profile_beat:
        cmd = ["docker", "compose", "--profile", "beat", "up", "-d", "--scale", f"backend={backend_replicas}"]
    return subprocess.run(cmd, cwd=ROOT, env=run_env).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto LAN IP + Docker start (host nginx for HTTP/S)")
    parser.add_argument("--ip", help="Override detected LAN IP")
    parser.add_argument("--build", action="store_true", help="Rebuild backend/celery images before up")
    parser.add_argument(
        "--backend-replicas",
        type=int,
        default=None,
        help="API replicas (default: BACKEND_REPLICAS in .env or 1); Docker LB on 127.0.0.1:8000",
    )
    parser.add_argument(
        "--beat",
        action="store_true",
        help="Also start celery-beat (daily Telegram report schedule)",
    )
    parser.add_argument("--no-up", action="store_true", help="Only refresh .env, do not start containers")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="After start, re-detect IP every 60s and print if it changed (no restart needed)",
    )
    args = parser.parse_args()

    def refresh() -> tuple[str, str, int] | None:
        host_ip = (args.ip or "").strip() or detect_lan_ipv4()
        if not host_ip:
            return None
        replicas = args.backend_replicas if args.backend_replicas is not None else _read_backend_replicas()
        url = write_compose_env(host_ip=host_ip, backend_replicas=replicas)
        return host_ip, url, replicas

    first = refresh()
    if not first:
        print("Could not detect LAN IP. Check network or use: --ip 192.168.1.20")
        return 1

    host_ip, public_url, backend_replicas = first
    print(f"LAN URL (via host nginx): {public_url}")
    print("Docker API only: http://127.0.0.1:8000 (configure host nginx to proxy — see host-nginx-examples/)")
    print("API/CORS: CORS_ALLOW_LAN=true — set CORS_ORIGINS in Backend/.env for production HTTPS domain.")
    if backend_replicas > 1:
        print(f"Docker: {backend_replicas} backend containers (published as 127.0.0.1:8000)")

    if not args.no_up:
        print("Starting Docker...")
        code = compose_up(
            build=args.build,
            profile_beat=args.beat,
            backend_replicas=backend_replicas,
        )
        if code != 0:
            return code
        print("Done. Open the LAN URL above after host nginx is configured.")
        print("Services: backend, db, redis, celery-worker, celery-beat, telegram-bot")
        print("After code changes: python scripts/deploy_lan.py --build")
        print("Telegram: docker compose logs telegram-bot -f")
        print("Health: curl http://127.0.0.1:8000/health")

    if not args.watch:
        return 0

    last_ip = host_ip
    print("Watching for IP changes (Ctrl+C to stop). Containers keep running.")
    try:
        while True:
            time.sleep(60)
            if args.ip:
                continue
            current = detect_lan_ipv4()
            if current and current != last_ip:
                last_ip = current
                url = write_compose_env(
                    host_ip=current,
                    backend_replicas=_read_backend_replicas(),
                )
                print(f"[IP changed] New LAN URL: {url}")
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
