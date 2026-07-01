"""Presentation helpers for rendering entries (dates and titles)."""
from __future__ import annotations

from datetime import datetime, timezone


def humandate(value: str | None, *, now: datetime | None = None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ref = (now or datetime.now(timezone.utc)).astimezone(dt.tzinfo)
    days = (ref.date() - dt.date()).days
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def entry_title(
    subject: str | None,
    recipients: list | None,
    captured_at: str | None,
    rec_map: dict | None = None,
    *,
    now: datetime | None = None,
) -> str:
    """A display title for an entry.

    Uses the real subject when there is one; otherwise composes a title from the
    recipients (mapped to their labels) and the humanized capture date, e.g.
    "Family · Today". Falls back to just the date, then to "Untitled"."""
    s = (subject or "").strip()
    if s and s != "(untitled)":
        return s
    rec_map = rec_map or {}
    labels = [rec_map.get(r, str(r).capitalize()) for r in (recipients or [])]
    date = humandate(captured_at, now=now)
    parts = []
    if labels:
        parts.append(", ".join(labels))
    if date:
        parts.append(date)
    return " · ".join(parts) or "Untitled"
