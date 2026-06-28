import io, json
from fastapi.testclient import TestClient
from storitad_web import app as appmod, config

def _client(tmp_path):
    cfg = config.AppConfig(
        archive_root=tmp_path, staging=tmp_path / "staging",
        trash=tmp_path / "trash", owners=["b@rry.im"],
        recipients_path=tmp_path / "r.json",
    )
    c = TestClient(appmod.create_app(cfg, enqueue=lambda e: None))
    c.headers.update({"X-Auth-Request-Email": "b@rry.im"})
    return c, cfg

def _capture(c):
    meta = {"subject": "orig", "mediaType": "VOICE", "mimeType": "audio/mp4",
            "durationSeconds": 3, "timezone": "UTC", "recipients": ["family"],
            "capturedAt": "2026-01-02T09:08:07Z"}
    return c.post("/api/entries", data={"meta": json.dumps(meta)},
                  files={"media": ("c.m4a", io.BytesIO(b"audio"), "audio/mp4")}).json()["id"]

def test_edit_updates_subject_and_notes(tmp_path):
    c, cfg = _client(tmp_path)
    eid = _capture(c)
    r = c.put(f"/api/entries/{eid}", json={"subject": "edited", "notes": "new note"})
    assert r.status_code == 204
    text = (cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md").read_text()
    assert "subject: edited" in text and "new note" in text

def test_edit_transcript(tmp_path):
    c, cfg = _client(tmp_path)
    eid = _capture(c)
    c.put(f"/api/entries/{eid}", json={"transcript": "corrected words"})
    text = (cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md").read_text()
    assert "corrected words" in text

def test_delete_moves_to_trash(tmp_path):
    c, cfg = _client(tmp_path)
    eid = _capture(c)
    r = c.delete(f"/api/entries/{eid}")
    assert r.status_code == 204
    assert not (cfg.archive_root / "entries" / "2026" / "01" / f"{eid}.md").exists()
    assert (cfg.trash / "2026" / "01" / f"{eid}.md").exists()
    assert (cfg.trash / "2026" / "01" / f"{eid}.m4a").exists()

def test_edit_missing_entry_404(tmp_path):
    c, _ = _client(tmp_path)
    r = c.put("/api/entries/nope", json={"subject": "x"})
    assert r.status_code == 404
