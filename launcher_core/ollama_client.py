from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_OLLAMA_CONFIG = {
    "ollama_url": "http://127.0.0.1:11434",
    "fast_model": "llama3.1:8b",
    "default_model": "qwen3:14b",
    "deep_model": "qwen3.6:35b-a3b-q4_K_M",
    "embedding_model": "nomic-embed-text:latest",
}


def load_ollama_config(base_dir: Path) -> dict[str, Any]:
    path = base_dir / "ai" / "ollama.json"
    if not path.exists():
        return DEFAULT_OLLAMA_CONFIG.copy()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_OLLAMA_CONFIG, **data}
    except (json.JSONDecodeError, OSError):
        return DEFAULT_OLLAMA_CONFIG.copy()


def generate(config: dict[str, Any], prompt: str, model_key: str = "default_model") -> tuple[bool, str]:
    model = str(config.get(model_key) or config["default_model"])
    url = str(config.get("ollama_url", DEFAULT_OLLAMA_CONFIG["ollama_url"])).rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        return True, str(data.get("response", "")).strip()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"Ollama に接続できませんでした: {exc}"

