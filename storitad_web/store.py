from __future__ import annotations

from pathlib import Path

from .ingest import render_markdown
from .ingest.sidecar import Sidecar
from .config import AppConfig


def write_capture(cfg: AppConfig, sc: Sidecar, media_bytes: bytes, author: str) -> Path:
    cfg.staging.mkdir(parents=True, exist_ok=True)
    media_src = cfg.staging / sc.media_file
    media_src.write_bytes(media_bytes)
    md = render_markdown.write_entry(
        cfg.archive_root, sc, media_src,
        server_transcript=None, server_model=None, author=author,
    )
    return md
