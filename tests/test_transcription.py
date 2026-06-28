from datetime import datetime, timezone
from storitad_web import transcription, config, entries, store

def _cfg(tmp_path):
    return config.AppConfig(
        archive_root=tmp_path, staging=tmp_path / "staging",
        trash=tmp_path / "trash", owners=["b@rry.im"],
        whisper_model=str(tmp_path / "model.bin"),
        recipients_path=tmp_path / "r.json",
    )

def _make_entry(cfg) -> str:
    cm = entries.CaptureMeta(
        subject="t", media_type="VOICE", mime_type="audio/mp4",
        duration_seconds=2, timezone="UTC", recipients=["family"],
        mood=None, tags=[], notes=None, location=None,
        captured_at=datetime(2026, 1, 2, 9, 8, 7, tzinfo=timezone.utc),
        author="b@rry.im",
    )
    sc = entries.synthesize_sidecar(cm, cfg.staging)
    store.write_capture(cfg, sc, b"audio", author="b@rry.im")
    return sc.id

def test_fill_transcript_rewrites_section(tmp_path):
    cfg = _cfg(tmp_path)
    eid = _make_entry(cfg)
    ok = transcription.fill_transcript(cfg, eid, transcribe_fn=lambda media, c: "hello there")
    assert ok
    md = cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md"
    text = md.read_text()
    assert "hello there" in text
    assert "transcript_model" in text

def test_pending_ids_detects_no_transcript(tmp_path):
    cfg = _cfg(tmp_path)
    eid = _make_entry(cfg)
    assert eid in transcription.pending_ids(cfg)

def test_pending_ids_excludes_filled(tmp_path):
    cfg = _cfg(tmp_path)
    eid = _make_entry(cfg)
    transcription.fill_transcript(cfg, eid, transcribe_fn=lambda media, c: "done")
    assert eid not in transcription.pending_ids(cfg)

def test_worker_drains_and_stops(tmp_path):
    import asyncio
    from storitad_web.transcription import Worker

    cfg = _cfg(tmp_path)
    eid = _make_entry(cfg)

    async def run():
        w = Worker(cfg, transcribe_fn=lambda media, c: "worker said hi")
        w.start()
        await w.queue.join()
        await w.stop()

    asyncio.run(run())

    md = cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md"
    assert "worker said hi" in md.read_text()
