import io, json
from fastapi.testclient import TestClient
from storitad_web import app as appmod, config

def _client(tmp_path):
    cfg = config.AppConfig(
        archive_root=tmp_path, staging=tmp_path / "staging",
        trash=tmp_path / "trash", owners=["b@rry.im"],
        recipients_path=tmp_path / "recipients.json",
    )
    c = TestClient(appmod.create_app(cfg, enqueue=lambda e: None))
    c.headers.update({"X-Auth-Request-Email": "b@rry.im"})
    return c, cfg

def test_recipients_default(tmp_path):
    c, _ = _client(tmp_path)
    r = c.get("/api/recipients")
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()]
    assert "family" in ids

def test_recent_tags(tmp_path):
    c, _ = _client(tmp_path)
    meta = {"subject": "s", "mediaType": "VOICE", "mimeType": "audio/mp4",
            "durationSeconds": 3, "timezone": "UTC", "recipients": ["family"],
            "tags": ["school", "daily"], "capturedAt": "2026-01-02T09:08:07Z"}
    c.post("/api/entries", data={"meta": json.dumps(meta)},
           files={"media": ("c.m4a", io.BytesIO(b"a"), "audio/mp4")})
    r = c.get("/api/recent-tags")
    assert r.status_code == 200
    assert "school" in r.json()

def test_capture_screen_renders(tmp_path):
    c, _ = _client(tmp_path)
    r = c.get("/")
    assert r.status_code == 200
    assert "record" in r.text.lower()
