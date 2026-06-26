# tests/test_render_markdown_author.py
from storitad_web.ingest import render_markdown
from storitad_web.ingest.sidecar import Sidecar

def _sidecar(tmp_path) -> Sidecar:
    raw = {
        "id": "20260101-120000-voice", "version": 2,
        "capturedAt": "2026-01-01T12:00:00Z", "durationSeconds": 5,
        "timezone": "Europe/London", "mediaFile": "20260101-120000-voice.m4a",
        "mediaType": "VOICE", "mimeType": "audio/mp4", "subject": "Hi",
        "device": "web", "appVersion": "1.0", "recipients": ["family"],
    }
    return Sidecar(raw=raw, path=tmp_path / "20260101-120000-voice.json")

def test_author_in_frontmatter_when_set(tmp_path):
    media = tmp_path / "20260101-120000-voice.m4a"
    media.write_bytes(b"x")
    md = render_markdown.write_entry(
        tmp_path, _sidecar(tmp_path), media, None, None, author="b@rry.im")
    assert "author: b@rry.im" in md.read_text()

def test_author_absent_when_none(tmp_path):
    media = tmp_path / "20260101-120000-voice.m4a"
    media.write_bytes(b"x")
    md = render_markdown.write_entry(tmp_path, _sidecar(tmp_path), media, None, None)
    assert "author:" not in md.read_text()
