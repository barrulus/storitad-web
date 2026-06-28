import io, json
from fastapi.testclient import TestClient
from storitad_web import app as appmod, config

def _client(tmp_path, enqueued):
    cfg = config.AppConfig(
        archive_root=tmp_path, staging=tmp_path / "staging",
        trash=tmp_path / "trash", owners=["b@rry.im"],
        recipients_path=tmp_path / "recipients.json",
    )
    application = appmod.create_app(cfg, enqueue=lambda eid: enqueued.append(eid))
    client = TestClient(application)
    client.headers.update({"X-Auth-Request-Email": "b@rry.im"})
    return client, cfg

def test_post_entry_writes_markdown_and_enqueues(tmp_path):
    enqueued = []
    client, cfg = _client(tmp_path, enqueued)
    meta = {
        "subject": "Picking up Casper", "mediaType": "VOICE",
        "mimeType": "audio/mp4", "durationSeconds": 8,
        "timezone": "Europe/London", "recipients": ["family"],
        "mood": "happy", "tags": ["school"], "notes": "hi",
        "capturedAt": "2026-01-02T09:08:07Z", "appVersion": "0.1.0",
    }
    files = {"media": ("clip.m4a", io.BytesIO(b"fake-audio"), "audio/mp4")}
    r = client.post("/api/entries", data={"meta": json.dumps(meta)}, files=files)
    assert r.status_code == 201
    eid = r.json()["id"]
    assert eid == "20260102-090807-voice"
    assert enqueued == [eid]
    md = cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md"
    assert md.exists()
    text = md.read_text()
    assert "subject: Picking up Casper" in text
    assert "author: b@rry.im" in text
    assert (cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.m4a").exists()

def test_post_entry_rejects_non_owner(tmp_path):
    enqueued = []
    client, _ = _client(tmp_path, enqueued)
    client.headers.update({"X-Auth-Request-Email": "stranger@x.com"})
    files = {"media": ("c.m4a", io.BytesIO(b"x"), "audio/mp4")}
    r = client.post("/api/entries", data={"meta": json.dumps({})}, files=files)
    assert r.status_code == 403
