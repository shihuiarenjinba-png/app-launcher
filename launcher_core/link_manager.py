from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_path(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"見つかりません: {path}"
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer", str(path)])
        elif sys.platform == "darwin":  # type: ignore[name-defined]
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True, f"開きました: {path}"
    except OSError as exc:
        return False, f"開けませんでした: {exc}"


def describe_path(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        item = path
        if item.is_dir():
            return "folder"
        return "file"
    except OSError:
        return "unknown"
