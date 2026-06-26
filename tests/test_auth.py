import pytest
from fastapi import HTTPException
from starlette.requests import Request
from storitad_web import auth

def _request(headers: dict) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})

def test_owner_accepted(monkeypatch):
    monkeypatch.setattr(auth, "_owners", lambda: ["b@rry.im"])
    assert auth.require_owner(_request({"X-Auth-Request-Email": "b@rry.im"})) == "b@rry.im"

def test_non_owner_rejected(monkeypatch):
    monkeypatch.setattr(auth, "_owners", lambda: ["b@rry.im"])
    with pytest.raises(HTTPException) as e:
        auth.require_owner(_request({"X-Auth-Request-Email": "stranger@x.com"}))
    assert e.value.status_code == 403

def test_missing_header_rejected(monkeypatch):
    monkeypatch.setattr(auth, "_owners", lambda: ["b@rry.im"])
    with pytest.raises(HTTPException) as e:
        auth.require_owner(_request({}))
    assert e.value.status_code == 403
