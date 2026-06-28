from __future__ import annotations

import json
from .config import AppConfig

_DEFAULT = [
    {"id": "partner", "label": "Partner", "emoji": "💛"},
    {"id": "child",   "label": "Child",   "emoji": "🧒"},
    {"id": "family",  "label": "Family",  "emoji": "🏠"},
    {"id": "friends", "label": "Friends", "emoji": "🤝"},
    {"id": "general", "label": "General", "emoji": "📝"},
]


def load(cfg: AppConfig) -> list[dict]:
    if cfg.recipients_path.exists():
        data = json.loads(cfg.recipients_path.read_text())
        return data.get("recipients", _DEFAULT)
    return _DEFAULT
