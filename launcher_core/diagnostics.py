from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def tail_text(path: Path, max_lines: int = 80) -> str:
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-max_lines:])


def build_log_prompt(app_name: str, log_text: str) -> str:
    return (
        "あなたはローカルStreamlitアプリの起動ログ診断係です。\n"
        "回答は日本語で、原因候補、確認ポイント、次の一手を短く整理してください。\n\n"
        f"アプリ名: {app_name}\n"
        "ログ:\n"
        "```text\n"
        f"{log_text}\n"
        "```"
    )


def find_port_conflicts(apps: Iterable) -> list[tuple[int, list[str]]]:
    """同じポートを複数アプリで使っている場合を検出して返す。

    戻り値: [(port, [app_name, app_name, ...]), ...] を port 昇順で。
    AppDefinition を想定するが、port と name 属性さえあれば動く。
    """
    by_port: dict[int, list[str]] = defaultdict(list)
    for app in apps:
        try:
            port = int(getattr(app, "port"))
        except (AttributeError, TypeError, ValueError):
            continue
        name = getattr(app, "name", getattr(app, "id", "(unknown)"))
        by_port[port].append(str(name))
    conflicts = [(p, names) for p, names in by_port.items() if len(names) > 1]
    conflicts.sort(key=lambda x: x[0])
    return conflicts


def find_broken_registry_files(registry_dir: Path) -> list[tuple[Path, str]]:
    """app-registry/*.json を1つずつ検査し、JSON として読めないものを返す。

    戻り値: [(path, error_message), ...]
    """
    broken: list[tuple[Path, str]] = []
    if not registry_dir.exists():
        return broken
    for path in sorted(registry_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                broken.append((path, "JSON のトップレベルがオブジェクトではありません"))
                continue
            if not data.get("entry"):
                broken.append((path, "`entry` フィールドがありません"))
        except json.JSONDecodeError as exc:
            broken.append((path, f"JSON 構文エラー: {exc.msg} (line {exc.lineno}, col {exc.colno})"))
        except OSError as exc:
            broken.append((path, f"読み込み失敗: {exc}"))
    return broken


def find_missing_entries(apps: Iterable) -> list[tuple[str, Path]]:
    """entry ファイルが存在しないアプリを検出する。

    戻り値: [(app_name, entry_path), ...]
    """
    missing: list[tuple[str, Path]] = []
    for app in apps:
        entry = getattr(app, "entry", None)
        if entry is None:
            continue
        if not Path(entry).exists():
            name = getattr(app, "name", getattr(app, "id", "(unknown)"))
            missing.append((str(name), Path(entry)))
    return missing


def simple_path_notes(path: Path, protected: bool = False) -> list[str]:
    notes: list[str] = []
    lower = str(path).lower()
    if protected:
        notes.append("保護対象です。自動削除候補にはしません。")
    if "__pycache__" in lower or path.suffix == ".pyc":
        notes.append("Pythonの自動生成キャッシュです。再生成できます。")
    if path.name in {".venv", "venv"}:
        notes.append("仮想環境です。再作成可能ですが、削除するとそのままでは起動できません。")
    if path.name in {"logs", "log"}:
        notes.append("ログフォルダです。古いログは整理候補です。")
    if path.name in {"work", "output"}:
        notes.append("実行結果フォルダです。中身の確認後に整理候補になります。")
    return notes

