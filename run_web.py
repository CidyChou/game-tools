#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"


def ensure_project_python() -> None:
    if not VENV_PYTHON.exists():
        return

    if Path(sys.prefix) != PROJECT_DIR / ".venv":
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


def get_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 PNG Tools Web 工具台。")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0，允许局域网访问。")
    parser.add_argument("--port", default=8000, type=int, help="监听端口，默认 8000。")
    parser.add_argument("--no-reload", action="store_true", help="关闭开发模式自动重载。")
    return parser.parse_args()


def main() -> None:
    ensure_project_python()

    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        if exc.name != "uvicorn":
            raise
        print("缺少依赖 uvicorn。请先安装项目依赖：")
        print("  python3 -m venv .venv")
        print("  .venv/bin/python -m pip install -r requirements.txt")
        raise SystemExit(1) from exc

    args = parse_args()
    lan_ip = get_lan_ip()

    print("PNG Tools Web")
    print(f"Local:   http://127.0.0.1:{args.port}/")
    print(f"LAN:     http://{lan_ip}:{args.port}/")
    print(f"Binding: {args.host}:{args.port}")

    uvicorn.run(
        "web_app:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
