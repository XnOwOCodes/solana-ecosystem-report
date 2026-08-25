from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    with cfg_path.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg["_root"] = str(ROOT)
    cfg["_config_path"] = str(cfg_path)
    return cfg


def resolve(cfg: dict[str, Any], key: str) -> Path:
    return (ROOT / cfg[key]).resolve()
