#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import os
import socket
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"
REQUIRED_MODULES = ("uvicorn", "multipart")


def in_project_venv() -> bool:
    return Path(sys.prefix).resolve() == (PROJECT_DIR / ".venv").resolve()


def run_setup_command(command: list[str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.check_call(command, cwd=PROJECT_DIR)


def ensure_project_python() -> None:
    if not VENV_PYTHON.exists():
        print("未找到 .venv，正在用当前 python3 创建项目虚拟环境...", flush=True)
        run_setup_command([sys.executable, "-m", "venv", str(PROJECT_DIR / ".venv")])

    if not in_project_venv():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


def ensure_dependencies() -> None:
    missing_module = find_missing_required_module()
    if missing_module is None:
        return

    if not REQUIREMENTS_FILE.exists():
        print(f"缺少依赖 {missing_module}，且未找到 requirements.txt。", file=sys.stderr)
        raise SystemExit(1)

    print("缺少项目依赖，正在安装 requirements.txt...", flush=True)
    run_setup_command([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])

    missing_module = find_missing_required_module()
    if missing_module is not None:
        print(f"依赖安装后仍无法导入 {missing_module}，请检查 pip 输出。", file=sys.stderr)
        raise SystemExit(1)


def find_missing_required_module() -> str | None:
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            return module_name
    return None


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
    args = parse_args()
    ensure_project_python()
    ensure_dependencies()
    import uvicorn

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
