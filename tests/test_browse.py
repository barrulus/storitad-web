import io, json
from fastapi.testclient import TestClient
from storitad_web import app as appmod, config

def _client(tmp_path):
    cfg = config.AppConfig(
        archive_root=tmp_path, staging=tmp_path / "staging",
        trash=tmp_path / "trash", owners=["b@rry.im"],
        recipients_path=tmp_path / "recipients.json",
    )
    client = TestClient(appmod.create_app(cfg))
    client.headers.update({"X-Auth-Request-Email": "b@rry.im"})
    return client, cfg

def _capture(client, subject):
    meta = {"subject": subject, "mediaType": "VOICE", "mimeType": "audio/mp4",
            "durationSeconds": 3, "timezone": "UTC", "recipients": ["family"],
            "capturedAt": "2026-01-02T09:08:07Z"}
    return client.post("/api/entries",
                       data={"meta": json.dumps(meta)},
                       files={"media": ("c.m4a", io.BytesIO(b"audio"), "audio/mp4")})

def test_browse_lists_entry(tmp_path):
    client, _ = _client(tmp_path)
    _capture(client, "My first web entry")
    r = client.get("/entries")
    assert r.status_code == 200
    assert "My first web entry" in r.text

def test_detail_shows_entry(tmp_path):
    client, _ = _client(tmp_path)
    eid = _capture(client, "Detail subject").json()["id"]
    r = client.get(f"/entries/{eid}")
    assert r.status_code == 200
    assert "Detail subject" in r.text

def test_media_served(tmp_path):
    client, _ = _client(tmp_path)
    _capture(client, "x")
    r = client.get("/media/2026/01/20260102-090807-voice.m4a")
    assert r.status_code == 200
    assert r.content == b"audio"

def test_media_requires_owner(tmp_path):
    client, _ = _client(tmp_path)
    _capture(client, "x")
    client.headers.update({"X-Auth-Request-Email": "stranger@x.com"})
    r = client.get("/media/2026/01/20260102-090807-voice.m4a")
    assert r.status_code == 403

def test_media_no_path_traversal(tmp_path):
    client, cfg = _client(tmp_path)
    _capture(client, "x")
    # plant a secret OUTSIDE the entries dir to prove it is never served
    secret = cfg.archive_root / "secret.txt"
    secret.write_text("TOPSECRET")
    for bad in [
        "/media/../../secret.txt",
        "/media/2026/01/%2e%2e%2f%2e%2e%2fsecret.txt",
        "/media/2026/01/..%2f..%2fsecret.txt",
    ]:
        r = client.get(bad)
        assert r.status_code == 404, f"{bad} -> {r.status_code}"
        assert "TOPSECRET" not in r.text

def test_root_route_renders(tmp_path):
    assert _client(tmp_path)[0].get("/").status_code == 200
