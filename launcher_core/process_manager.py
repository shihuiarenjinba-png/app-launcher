from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from .registry import AppDefinition


def load_pids(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_pids(path: Path, pids: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(pids, f, ensure_ascii=False, indent=2)


def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def reconcile_pids(path: Path, pids: dict[str, Any]) -> dict[str, Any]:
    alive = {
        app_id: info
        for app_id, info in pids.items()
        if is_pid_alive(int(info.get("pid", 0)))
    }
    if alive != pids:
        save_pids(path, alive)
    return alive


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def resolve_python(spec: str | None) -> str:
    if not spec:
        return sys.executable

    candidate = Path(spec)
    if candidate.is_absolute() and candidate.exists():
        return str(candidate)

    if os.name == "nt":
        try:
            out = subprocess.run(
                ["py", f"-{spec}", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        command = f"python{spec}"
        try:
            out = subprocess.run(["which", command], capture_output=True, text=True, timeout=5)
            if out.returncode == 0 and out.stdout.strip():
                return command
        except (OSError, subprocess.TimeoutExpired):
            pass

    return sys.executable


def start_app(app: AppDefinition, pid_path: Path, log_dir: Path, host: str) -> tuple[bool, str]:
    if app.type != "streamlit":
        return False, f"未対応のアプリ種別です: {app.type}"
    if not app.entry.exists():
        return False, f"起動ファイルが見つかりません: {app.entry}"
    if port_in_use(app.port):
        return False, f"ポート {app.port} はすでに使用中です"

    python_exe = resolve_python(app.python)
    log_dir.mkdir(exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in app.id)
    log_path = log_dir / f"{safe_name}.log"
    log_fp = log_path.open("a", encoding="utf-8", buffering=1)
    log_fp.write(f"\n--- start: {app.name} ({host}:{app.port}, python={python_exe}) ---\n")

    creationflags = 0
    if os.name == "nt":
        detached_process = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | detached_process

    proc = subprocess.Popen(
        [
            python_exe,
            "-m",
            "streamlit",
            "run",
            str(app.entry),
            "--server.port",
            str(app.port),
            "--server.address",
            "0.0.0.0",
            "--server.headless",
            "true",
        ],
        cwd=str(app.cwd),
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )

    pids = load_pids(pid_path)
    pids[app.id] = {
        "pid": proc.pid,
        "name": app.name,
        "port": app.port,
        "host": host,
        "log": str(log_path),
        "python": python_exe,
        "entry": str(app.entry),
    }
    save_pids(pid_path, pids)
    return True, f"{app.name} を起動しました (PID {proc.pid})"


def stop_app(app: AppDefinition, pid_path: Path) -> tuple[bool, str]:
    pids = load_pids(pid_path)
    info = pids.get(app.id)
    if not info:
        return False, "起動情報がありません"

    pid = int(info.get("pid", 0))
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
        else:
            os.kill(pid, 15)
    except (OSError, subprocess.TimeoutExpired):
        pass

    pids.pop(app.id, None)
    save_pids(pid_path, pids)
    return True, f"{app.name} を停止しました (PID {pid})"

