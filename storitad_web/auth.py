"""Trust the proxy-injected identity header; enforce an owner allowlist.

oauth2-proxy (in front of this app) authenticates against pocket-id and sets
X-Auth-Request-Email. The app binds loopback-only and is only reachable via
Caddy forward_auth, so the header is trustworthy; the allowlist is defence in
depth and the seam for future multi-user."""
from __future__ import annotations

from fastapi import HTTPException, Request

from . import config

OWNER_HEADER = "x-auth-request-email"
_cfg = config.load()


def _owners() -> list[str]:
    return _cfg.owners


def make_require_owner(owners: list[str]):
    """Return a FastAPI dependency that authorises against `owners`."""
    allowed = [o.lower() for o in owners]
    def _require_owner(request: Request) -> str:
        email = request.headers.get(OWNER_HEADER, "").strip().lower()
        if email and email in allowed:
            return email
        raise HTTPException(status_code=403, detail="not an owner")
    return _require_owner


def require_owner(request: Request) -> str:
    return make_require_owner(_owners())(request)
