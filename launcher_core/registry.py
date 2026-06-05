from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppLink:
    label: str
    path: Path
    kind: str = "path"


@dataclass(slots=True)
class AppDefinition:
    id: str
    name: str
    category: str
    type: str
    entry: Path
    cwd: Path
    port: int
    python: str | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    links: list[AppLink] = field(default_factory=list)
    ai: dict[str, bool] = field(default_factory=dict)
    protected: bool = False
    favorite: bool = False
    hidden: bool = False
    merged_into: str | None = None
    status: str = "active"
    priority: int = 100
    source: Path | None = None


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _resolve(base_dir: Path, value: str | None, fallback: Path | None = None) -> Path:
    if not value:
        if fallback is None:
            raise ValueError("path value is required")
        return fallback
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def load_launcher_config(base_dir: Path) -> dict[str, Any]:
    config_path = base_dir / "config.json"
    if not config_path.exists():
        return {"host": "127.0.0.1", "base_port": 8502, "apps": []}
    return _load_json(config_path)


def load_registry_apps(base_dir: Path, registry_dir: Path, include_hidden: bool = False) -> list[AppDefinition]:
    if not registry_dir.exists():
        return []

    apps: list[AppDefinition] = []
    for path in sorted(registry_dir.glob("*.json")):
        try:
            raw = _load_json(path)
            if bool(raw.get("hidden", False)) and not include_hidden:
                continue

            app_id = str(raw.get("id") or path.stem)
            entry = _resolve(base_dir, str(raw.get("entry", "")))
            cwd = _resolve(base_dir, raw.get("cwd"), fallback=entry.parent)
            links = [
                AppLink(
                    label=str(link.get("label", "リンク")),
                    path=_resolve(base_dir, str(link.get("path", ""))),
                    kind=str(link.get("kind", "path")),
                )
                for link in raw.get("links", [])
                if isinstance(link, dict) and link.get("path")
            ]
            apps.append(
                AppDefinition(
                    id=app_id,
                    name=str(raw.get("name") or app_id),
                    category=str(raw.get("category") or "Other"),
                    type=str(raw.get("type") or "streamlit"),
                    entry=entry,
                    cwd=cwd,
                    port=int(raw.get("port", 8502)),
                    python=raw.get("python"),
                    description=str(raw.get("description") or ""),
                    tags=[str(tag) for tag in raw.get("tags", [])],
                    links=links,
                    ai=dict(raw.get("ai", {})),
                    protected=bool(raw.get("protected", False)),
                    favorite=bool(raw.get("favorite", False)),
                    hidden=bool(raw.get("hidden", False)),
                    merged_into=raw.get("merged_into"),
                    status=str(raw.get("status") or "active"),
                    priority=int(raw.get("priority", 100)),
                    source=path,
                )
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            # 壊れた / 不完全な 1 ファイルでランチャー全体が落ちないようにスキップ。
            # 詳細は diagnostics.find_broken_registry_files で別途検出される。
            continue
    return apps


def fallback_apps_from_config(base_dir: Path, config: dict[str, Any]) -> list[AppDefinition]:
    base_port = int(config.get("base_port", 8502))
    apps: list[AppDefinition] = []
    for index, raw in enumerate(config.get("apps", [])):
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or f"App {index + 1}")
        entry = _resolve(base_dir, str(raw.get("file", "")))
        app_id = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
        apps.append(
            AppDefinition(
                id=app_id or f"app-{index + 1}",
                name=name,
                category="Legacy Config",
                type="streamlit",
                entry=entry,
                cwd=entry.parent,
                port=int(raw.get("port", base_port + index)),
                python=raw.get("python"),
                description="config.json から読み込んだ既存登録です。",
                links=[AppLink("アプリフォルダ", entry.parent)],
                ai={"logDiagnosis": True},
                protected="research" in str(raw.get("file", "")).lower(),
                priority=100 + index,
                source=base_dir / "config.json",
            )
        )
    return apps


def load_apps(base_dir: Path) -> tuple[dict[str, Any], list[AppDefinition]]:
    config = load_launcher_config(base_dir)
    registry_apps = load_registry_apps(base_dir, base_dir / "app-registry")
    apps = registry_apps or fallback_apps_from_config(base_dir, config)
    apps.sort(key=lambda app: (not app.favorite, app.category.lower(), app.priority, app.name.lower()))
    return config, apps

