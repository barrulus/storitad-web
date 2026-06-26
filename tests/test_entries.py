# tests/test_entries.py
from datetime import datetime, timezone
from storitad_web import entries

def _meta(**kw):
    base = dict(
        subject="Hello world", media_type="VOICE", mime_type="audio/mp4",
        duration_seconds=12, timezone="Europe/London", recipients=["family"],
        mood="happy", tags=["test"], notes="a note", location=None,
        captured_at=datetime(2026, 1, 2, 9, 8, 7, tzinfo=timezone.utc),
        author="b@rry.im", app_version="0.1.0",
    )
    base.update(kw)
    return entries.CaptureMeta(**base)

def test_make_entry_id_voice():
    ts = datetime(2026, 1, 2, 9, 8, 7, tzinfo=timezone.utc)
    assert entries.make_entry_id(ts, "VOICE") == "20260102-090807-voice"

def test_make_entry_id_video():
    ts = datetime(2026, 1, 2, 9, 8, 7, tzinfo=timezone.utc)
    assert entries.make_entry_id(ts, "VIDEO") == "20260102-090807-video"

def test_synthesize_sidecar_has_required_fields(tmp_path):
    from storitad_web.ingest.sidecar import REQUIRED_FIELDS
    sc = entries.synthesize_sidecar(_meta(), tmp_path)
    for f in REQUIRED_FIELDS:
        assert f in sc.raw
    assert sc.raw["device"] == "web"
    assert sc.raw["author"] == "b@rry.im"
    assert sc.media_file == "20260102-090807-voice.m4a"
    assert (tmp_path / "20260102-090807-voice.json").exists()

def test_synthesize_sidecar_video_ext(tmp_path):
    sc = entries.synthesize_sidecar(_meta(media_type="VIDEO", mime_type="video/mp4"), tmp_path)
    assert sc.media_file.endswith(".mp4")

def test_capturedat_is_iso_z(tmp_path):
    sc = entries.synthesize_sidecar(_meta(), tmp_path)
    assert sc.raw["capturedAt"] == "2026-01-02T09:08:07Z"
