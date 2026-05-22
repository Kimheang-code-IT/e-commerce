#!/usr/bin/env python3
"""
Auto-detect LAN IPv4 and start Docker (no manual IP in config files).

  python scripts/deploy_lan.py          # detect IP + docker compose up -d
  python scripts/deploy_lan.py --build  # also rebuild images
  python scripts/deploy_lan.py --watch  # keep printing URL if DHCP changes IP

Or double-click / run: start-lan.ps1
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def pick_http_port(preferred: int) -> int:
    """Use preferred port, or the next free one (never binds host port 80)."""
    for candidate in range(preferred, preferred + 30):
        if port_available(candidate):
            if candidate != preferred:
                print(f"Port {preferred} is in use; using {candidate} instead.")
            return candidate
    print(f"Warning: could not find a free port near {preferred}; trying {preferred} anyway.")
    return preferred


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
    """BACKEND_REPLICAS from root .env (default 1). Nginx load-balances when > 1."""
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BACKEND_REPLICAS="):
                try:
                    return max(1, int(line.split("=", 1)[1].strip()))
                except ValueError:
                    break
    return 1


def write_compose_env(*, host_ip: str, http_port: int, https_port: int, backend_replicas: int) -> str:
    public_url = f"http://{host_ip}:{http_port}"
    lines = [
        "# Auto-generated — do not edit; regenerated on each start (scripts/deploy_lan.py).",
        "# Docker volume prefix: e-commerce_pg_data (set e-comerce after folder rename only).",
        "COMPOSE_PROJECT_NAME=e-commerce",
        f"HOST_LAN_IP={host_ip}",
        f"PUBLIC_HTTP_PORT={http_port}",
        f"PUBLIC_HTTPS_PORT={https_port}",
        f"BACKEND_REPLICAS={backend_replicas}",
        "CORS_ALLOW_LAN=true",
        "NUXT_PUBLIC_SITE_URL=",
        "NUXT_PUBLIC_API_BASE=/api/v1",
        "NUXT_PUBLIC_USE_BACKEND_API=true",
        "FILE_BASE_URL=",
        "",
        f"# Wi-Fi URL: {public_url}/",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return public_url


COMPOSE_BUILD_SERVICES = [
    "backend",
    "celery-worker",
    "celery-beat",
    "telegram-bot",
    "nginx",
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
    if build:
        print("Building:", ", ".join(COMPOSE_BUILD_SERVICES))
        code = subprocess.run(
            ["docker", "compose", "build", *COMPOSE_BUILD_SERVICES],
            cwd=ROOT,
        ).returncode
        if code != 0:
            return code
    cmd = ["docker", "compose", "up", "-d", "--scale", f"backend={backend_replicas}"]
    if profile_beat:
        cmd = ["docker", "compose", "--profile", "beat", "up", "-d", "--scale", f"backend={backend_replicas}"]
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto LAN IP + Docker start (no manual IP config)")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--https-port", type=int, default=8443)
    parser.add_argument("--ip", help="Override detected LAN IP")
    parser.add_argument("--build", action="store_true", help="Rebuild backend/celery/nginx images before up")
    parser.add_argument(
        "--backend-replicas",
        type=int,
        default=None,
        help="API replicas behind nginx load balancer (default: BACKEND_REPLICAS in .env or 1)",
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
        http_port = pick_http_port(args.port)
        replicas = args.backend_replicas if args.backend_replicas is not None else _read_backend_replicas()
        url = write_compose_env(
            host_ip=host_ip,
            http_port=http_port,
            https_port=args.https_port,
            backend_replicas=replicas,
        )
        return host_ip, url, replicas

    first = refresh()
    if not first:
        print("Could not detect LAN IP. Check network or use: --ip 192.168.1.20")
        return 1

    host_ip, public_url, backend_replicas = first
    print(f"LAN URL (open on Wi-Fi devices): {public_url}/")
    print("API/CORS follow this IP automatically — no edits in Backend/.env when IP changes.")
    if backend_replicas > 1:
        print(f"Load balancer: nginx -> {backend_replicas} backend containers (least_conn)")

    if not args.no_up:
        print("Starting Docker...")
        code = compose_up(
            build=args.build,
            profile_beat=args.beat,
            backend_replicas=backend_replicas,
        )
        if code != 0:
            return code
        print("Done. Use the URL above on any device on the same Wi-Fi.")
        print("Services: nginx, backend, db, redis, celery-worker, celery-beat, telegram-bot")
        if args.beat:
            print("Also running: celery-beat (profile beat)")
        print("After code changes: python scripts/deploy_lan.py --build")
        print("Telegram: docker compose logs telegram-bot -f  (send /start; same token/chat in Backend/.env on every PC)")
        print("PDF: <LAN-URL>/api/v1/pos/invoice/<invoice-no>/pdf (auth required)")

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
                    http_port=args.port,
                    https_port=args.https_port,
                    backend_replicas=_read_backend_replicas(),
                )
                print(f"[IP changed] New URL: {url}/")
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
