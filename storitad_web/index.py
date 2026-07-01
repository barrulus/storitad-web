# storitad_web/index.py
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from . import recipients as recipients_mod
from .ingest import mdfile
from .config import AppConfig
from .display import entry_title


@dataclass
class EntrySummary:
    id: str
    subject: str
    title: str
    type: str
    captured_at: str
    recipients: list
    tags: list
    mood: str | None
    author: str | None
    media: str | None
    has_transcript: bool


def _recipient_labels(cfg: AppConfig) -> dict:
    return {r["id"]: r.get("label", r["id"]) for r in recipients_mod.load(cfg)}


def _entries_root(cfg: AppConfig) -> Path:
    return cfg.archive_root / "entries"


def list_entries(cfg: AppConfig) -> list[EntrySummary]:
    out: list[EntrySummary] = []
    root = _entries_root(cfg)
    if not root.exists():
        return out
    rec_map = _recipient_labels(cfg)
    for md in root.rglob("*.md"):
        fm, body = mdfile.load_fm(md)
        if not fm:
            continue
        transcript = _section(body, "Transcript")
        subject = fm.get("subject", "(untitled)")
        captured_at = str(fm.get("captured_at", ""))
        recips = fm.get("recipients", [])
        out.append(EntrySummary(
            id=fm.get("id", md.stem),
            subject=subject,
            title=entry_title(subject, recips, captured_at, rec_map),
            type=fm.get("type", "voice"),
            captured_at=captured_at,
            recipients=recips,
            tags=fm.get("tags", []),
            mood=fm.get("mood"),
            author=fm.get("author"),
            media=fm.get("media"),
            has_transcript=bool(transcript) and transcript != "(no transcript)",
        ))
    out.sort(key=lambda e: e.captured_at, reverse=True)
    return out


def recent_tags(cfg: AppConfig, limit: int = 12) -> list[str]:
    counter: Counter[str] = Counter()
    for e in list_entries(cfg):
        counter.update(e.tags)
    return [t for t, _ in counter.most_common(limit)]


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
        "title": entry_title(
            fm.get("subject"), fm.get("recipients", []),
            str(fm.get("captured_at", "")), _recipient_labels(cfg)),
        "transcript": _section(body, "Transcript"),
        "notes": _section(body, "Notes"),
        "media_rel": f"{rel}/{media}" if media else "",
        "media_url": f"/media/{rel}/{media}" if media else "",
    }
