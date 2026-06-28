# storitad_web/index.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ingest import mdfile
from .config import AppConfig


@dataclass
class EntrySummary:
    id: str
    subject: str
    type: str
    captured_at: str
    recipients: list
    tags: list
    mood: str | None
    author: str | None
    media: str | None


def _entries_root(cfg: AppConfig) -> Path:
    return cfg.archive_root / "entries"


def list_entries(cfg: AppConfig) -> list[EntrySummary]:
    out: list[EntrySummary] = []
    root = _entries_root(cfg)
    if not root.exists():
        return out
    for md in root.rglob("*.md"):
        fm, _ = mdfile.load_fm(md)
        if not fm:
            continue
        out.append(EntrySummary(
            id=fm.get("id", md.stem),
            subject=fm.get("subject", "(untitled)"),
            type=fm.get("type", "voice"),
            captured_at=str(fm.get("captured_at", "")),
            recipients=fm.get("recipients", []),
            tags=fm.get("tags", []),
            mood=fm.get("mood"),
            author=fm.get("author"),
            media=fm.get("media"),
        ))
    out.sort(key=lambda e: e.captured_at, reverse=True)
    return out


def _section(body: str, heading: str) -> str:
    target = f"## {heading}".lower()
    grab, chunk = False, []
    for line in body.splitlines():
        if line.strip().lower() == target:
            grab = True
            continue
        if grab and line.startswith("## "):
            break
        if grab:
            chunk.append(line)
    return "\n".join(chunk).strip()


def load_entry(cfg: AppConfig, entry_id: str) -> dict | None:
    md = mdfile.find_entry_md(_entries_root(cfg), entry_id)
    if md is None:
        return None
    fm, body = mdfile.load_fm(md)
    rel = md.relative_to(_entries_root(cfg)).parent  # e.g. 2026/01
    media = fm.get("media")
    return {
        "fm": fm,
        "transcript": _section(body, "Transcript"),
        "notes": _section(body, "Notes"),
        "media_rel": f"{rel}/{media}" if media else "",
        "media_url": f"/media/{rel}/{media}" if media else "",
    }
