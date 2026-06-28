from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile

from . import auth, store
from .config import AppConfig
from .entries import CaptureMeta, synthesize_sidecar


def _parse_captured_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def create_app(cfg: AppConfig, enqueue: Callable[[str], None] | None = None) -> FastAPI:
    enqueue = enqueue or (lambda _eid: None)
    application = FastAPI(title="Storitad Web")

    # Build a per-app owner dependency that uses cfg.owners (not the module-level default).
    def _require_owner(request: Request) -> str:
        email = request.headers.get(auth.OWNER_HEADER, "").strip().lower()
        if email and email in [o.lower() for o in cfg.owners]:
            return email
        raise HTTPException(status_code=403, detail="not an owner")

    @application.post("/api/entries", status_code=201)
    async def post_entry(
        meta: str = Form(...),
        media: UploadFile = File(...),
        owner: str = Depends(_require_owner),
    ):
        try:
            m = json.loads(meta)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="invalid meta json")
        cm = CaptureMeta(
            subject=str(m.get("subject", "")).strip() or "(untitled)",
            media_type=m.get("mediaType", "VOICE"),
            mime_type=m.get("mimeType", "audio/mp4"),
            duration_seconds=int(m.get("durationSeconds", 0)),
            timezone=m.get("timezone", "UTC"),
            recipients=list(m.get("recipients", [])),
            mood=m.get("mood"),
            tags=list(m.get("tags", [])),
            notes=m.get("notes"),
            location=m.get("location"),
            captured_at=_parse_captured_at(m.get("capturedAt")),
            author=owner,
            app_version=m.get("appVersion", "0.1.0"),
        )
        sc = synthesize_sidecar(cm, cfg.staging)
        media_bytes = await media.read()
        store.write_capture(cfg, sc, media_bytes, author=owner)
        enqueue(sc.id)
        return {"id": sc.id}

    application.state.cfg = cfg
    return application
