# storitad_web/entries.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .ingest import sidecar as sidecar_mod


@dataclass
class CaptureMeta:
    subject: str
    media_type: str           # "VOICE" | "VIDEO"
    mime_type: str
    duration_seconds: int
    timezone: str
    recipients: list[str]
    mood: str | None
    tags: list[str]
    notes: str | None
    location: dict | None
    captured_at: datetime
    author: str
    app_version: str = "0.1.0"
    device: str = "web"


def ext_for(media_type: str) -> str:
    return "mp4" if media_type.upper() == "VIDEO" else "m4a"


def make_entry_id(captured_at: datetime, media_type: str) -> str:
    ts = captured_at.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = "video" if media_type.upper() == "VIDEO" else "voice"
    return f"{ts}-{suffix}"


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def synthesize_sidecar(meta: CaptureMeta, staging_dir: Path) -> sidecar_mod.Sidecar:
    entry_id = make_entry_id(meta.captured_at, meta.media_type)
    media_file = f"{entry_id}.{ext_for(meta.media_type)}"
    raw = {
        "id": entry_id,
        "version": 2,
        "capturedAt": _iso_z(meta.captured_at),
        "durationSeconds": int(meta.duration_seconds),
        "timezone": meta.timezone,
        "mediaFile": media_file,
        "mediaType": meta.media_type.upper(),
        "mimeType": meta.mime_type,
        "subject": meta.subject,
        "author": meta.author,
        "recipients": list(meta.recipients) or ["family"],
        "mood": meta.mood,
        "tags": list(meta.tags),
        "notes": meta.notes,
        "device": meta.device,
        "appVersion": meta.app_version,
    }
    if meta.location:
        raw["location"] = meta.location
    staging_dir.mkdir(parents=True, exist_ok=True)
    json_path = staging_dir / f"{entry_id}.json"
    json_path.write_text(json.dumps(raw, indent=2))
    return sidecar_mod.load(json_path)
