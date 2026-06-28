from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

log = logging.getLogger(__name__)

from .ingest import mdfile
from .ingest.transcribe import TranscriberConfig, transcribe as _whisper
from .config import AppConfig

_EMPTY = {"", "(no transcript)", "(transcribing…)"}


def _entries_root(cfg: AppConfig) -> Path:
    return cfg.archive_root / "entries"


def _transcript_text(body: str) -> str:
    grab, chunk = False, []
    for line in body.splitlines():
        if line.strip().lower() == "## transcript":
            grab = True
            continue
        if grab and line.startswith("## "):
            break
        if grab:
            chunk.append(line)
    return "\n".join(chunk).strip()


def pending_ids(cfg: AppConfig) -> list[str]:
    out = []
    root = _entries_root(cfg)
    if not root.exists():
        return out
    for md in root.rglob("*.md"):
        fm, body = mdfile.load_fm(md)
        if _transcript_text(body) in _EMPTY:
            out.append(fm.get("id", md.stem))
    return out


def fill_transcript(
    cfg: AppConfig, entry_id: str,
    transcribe_fn: Callable[[Path, TranscriberConfig], str] = _whisper,
) -> bool:
    md = mdfile.find_entry_md(_entries_root(cfg), entry_id)
    if md is None:
        return False
    fm, body = mdfile.load_fm(md)
    media = fm.get("media")
    if not media:
        return False
    media_path = md.with_name(media)
    tcfg = TranscriberConfig(
        whisper_bin=cfg.whisper_bin, model_path=cfg.whisper_model,
        model_name=cfg.whisper_model_name,
    )
    text = transcribe_fn(media_path, tcfg).strip() or "(no speech detected)"
    body = mdfile.replace_section(body, "Transcript", text)
    fm["transcript_model"] = cfg.whisper_model_name
    mdfile.write_fm(md, fm, body)
    return True


class Worker:
    def __init__(self, cfg: AppConfig,
                 transcribe_fn: Callable[[Path, TranscriberConfig], str] = _whisper):
        self.cfg = cfg
        self.transcribe_fn = transcribe_fn
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def enqueue(self, entry_id: str) -> None:
        self.queue.put_nowait(entry_id)

    async def _run(self) -> None:
        while True:
            entry_id = await self.queue.get()
            try:
                await asyncio.to_thread(
                    fill_transcript, self.cfg, entry_id, self.transcribe_fn)
            except Exception:
                log.exception("transcription failed for %s", entry_id)
            finally:
                self.queue.task_done()

    def start(self) -> None:
        for eid in pending_ids(self.cfg):
            self.enqueue(eid)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
