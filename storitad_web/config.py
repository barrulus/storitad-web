from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


@dataclass
class AppConfig:
    archive_root: Path
    staging: Path
    trash: Path
    owners: list[str]
    whisper_bin: str = "whisper-cli"
    whisper_model: str = ""
    whisper_model_name: str = "whisper-small.en"
    recipients_path: Path = field(default_factory=lambda: Path("recipients.json"))
    port: int = 30100


def load(path: Path | None = None) -> AppConfig:
    data: dict = {}
    cfg_path = path or Path(
        os.environ.get("STORITAD_WEB_CONFIG", "~/.config/storitad/web.yml")
    ).expanduser()
    if cfg_path.exists():
        data = yaml.safe_load(cfg_path.read_text()) or {}
    root = _expand(data.get("archive_root", "/srv/data/storitad"))
    return AppConfig(
        archive_root=root,
        staging=_expand(data.get("staging", str(root / "staging"))),
        trash=_expand(data.get("trash", str(root / "trash"))),
        owners=list(data.get("owners", [])),
        whisper_bin=data.get("whisper_bin", "whisper-cli"),
        whisper_model=data.get("whisper_model", ""),
        whisper_model_name=data.get("whisper_model_name", "whisper-small.en"),
        recipients_path=_expand(data.get("recipients_path", str(root / "recipients.json"))),
        port=int(data.get("port", 30100)),
    )
