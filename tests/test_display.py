from datetime import datetime, timezone

from storitad_web.display import entry_title, humandate

_NOW = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
_REC = {"family": "Family", "partner": "Partner"}


def test_real_subject_wins():
    assert entry_title("Beach day", ["family"], "2026-06-30T09:00:00Z",
                       _REC, now=_NOW) == "Beach day"


def test_untitled_uses_recipients_and_date():
    assert entry_title("(untitled)", ["family"], "2026-06-30T09:00:00Z",
                       _REC, now=_NOW) == "Family · Today"


def test_empty_subject_multiple_recipients():
    assert entry_title("", ["family", "partner"], "2026-06-29T09:00:00Z",
                       _REC, now=_NOW) == "Family, Partner · Yesterday"


def test_unknown_recipient_id_is_capitalized():
    assert entry_title("", ["mum"], "2026-06-03T09:00:00Z",
                       _REC, now=_NOW) == "Mum · 3 Jun 2026"


def test_no_recipients_falls_back_to_date():
    assert entry_title("(untitled)", [], "2026-06-30T09:00:00Z",
                       _REC, now=_NOW) == "Today"


def test_no_subject_no_recipients_no_date():
    assert entry_title("", [], "", _REC, now=_NOW) == "Untitled"


def test_humandate_still_here():
    assert humandate("2026-06-30T08:00:00Z", now=_NOW) == "Today"
