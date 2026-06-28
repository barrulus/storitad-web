from __future__ import annotations

import shutil
from pathlib import Path

from .ingest import render_markdown
from .ingest import mdfile
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


def edit_entry(cfg: AppConfig, entry_id: str, payload: dict) -> bool:
    entries_root = cfg.archive_root / "entries"
    md = mdfile.find_entry_md(entries_root, entry_id)
    if md is None:
        return False
    fm, body = mdfile.load_fm(md)
    if "subject" in payload:
        fm["subject"] = str(payload["subject"]).strip() or fm.get("subject", "")
    if "mood" in payload:
        fm["mood"] = payload["mood"] or None
    if "recipients" in payload:
        fm["recipients"] = [str(r).strip() for r in payload["recipients"] if str(r).strip()]
    if "tags" in payload:
        fm["tags"] = [str(t).strip() for t in payload["tags"] if str(t).strip()]
    if "notes" in payload:
        body = mdfile.replace_section(body, "Notes", str(payload["notes"]).strip())
    if "transcript" in payload:
        body = mdfile.replace_section(body, "Transcript", str(payload["transcript"]).strip())
    mdfile.write_fm(md, fm, body)
    return True


def delete_entry(cfg: AppConfig, entry_id: str) -> bool:
    entries_root = cfg.archive_root / "entries"
    md = mdfile.find_entry_md(entries_root, entry_id)
    if md is None:
        return False
    rel = md.relative_to(entries_root).parent
    dest_dir = cfg.trash / rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    fm, _ = mdfile.load_fm(md)
    media_name = fm.get("media")
    shutil.move(str(md), str(dest_dir / md.name))
    if media_name:
        media = md.with_name(media_name)
        if media.exists():
            shutil.move(str(media), str(dest_dir / media_name))
    return True
