from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import auth, index, store
from .config import AppConfig
from .entries import CaptureMeta, synthesize_sidecar
from .transcription import Worker

_PKG_DIR = Path(__file__).resolve().parent


def _parse_captured_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def create_app(cfg: AppConfig, enqueue: Callable[[str], None] | None = None) -> FastAPI:
    if enqueue is None:
        worker = Worker(cfg)

        @asynccontextmanager
        async def lifespan(app):
            worker.start()
            yield
            await worker.stop()

        application = FastAPI(title="Storitad Web", lifespan=lifespan)
        enqueue = worker.enqueue
    else:
        application = FastAPI(title="Storitad Web")
    owner_dep = auth.make_require_owner(cfg.owners)

    @application.post("/api/entries", status_code=201)
    async def post_entry(
        meta: str = Form(...),
        media: UploadFile = File(...),
        owner: str = Depends(owner_dep),
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

    @application.put("/api/entries/{entry_id}", status_code=204)
    async def put_entry(entry_id: str, payload: dict, owner: str = Depends(owner_dep)):
        if not store.edit_entry(cfg, entry_id, payload):
            raise HTTPException(status_code=404, detail="entry not found")

    @application.delete("/api/entries/{entry_id}", status_code=204)
    async def delete_entry_route(entry_id: str, owner: str = Depends(owner_dep)):
        if not store.delete_entry(cfg, entry_id):
            raise HTTPException(status_code=404, detail="entry not found")

    templates = Jinja2Templates(directory=str(_PKG_DIR / "templates"))
    application.mount("/static", StaticFiles(directory=str(_PKG_DIR / "static")), name="static")

    from . import recipients as recipients_mod

    @application.get("/", response_class=HTMLResponse)
    async def capture_screen(request: Request, owner: str = Depends(owner_dep)):
        return templates.TemplateResponse(request, "capture.html", {})

    @application.get("/entries", response_class=HTMLResponse)
    async def browse(request: Request, owner: str = Depends(owner_dep)):
        return templates.TemplateResponse(
            request, "browse.html", {"entries": index.list_entries(cfg)})

    @application.get("/api/recipients")
    async def api_recipients(owner: str = Depends(owner_dep)):
        return recipients_mod.load(cfg)

    @application.get("/api/recent-tags")
    async def api_recent_tags(owner: str = Depends(owner_dep)):
        return index.recent_tags(cfg)

    @application.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
    async def edit_form(entry_id: str, request: Request, owner: str = Depends(owner_dep)):
        entry = index.load_entry(cfg, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="entry not found")
        return templates.TemplateResponse(request, "edit.html", {"entry": entry})

    @application.get("/entries/{entry_id}", response_class=HTMLResponse)
    async def detail(entry_id: str, request: Request, owner: str = Depends(owner_dep)):
        entry = index.load_entry(cfg, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="entry not found")
        return templates.TemplateResponse(request, "detail.html", {"entry": entry})

    @application.get("/media/{year}/{month}/{filename}")
    async def media(year: str, month: str, filename: str, owner: str = Depends(owner_dep)):
        path = (cfg.archive_root / "entries" / year / month / filename).resolve()
        root = (cfg.archive_root / "entries").resolve()
        if root not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="media not found")
        return FileResponse(path)

    application.state.cfg = cfg
    return application
