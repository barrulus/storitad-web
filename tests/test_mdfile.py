# tests/test_mdfile.py
from pathlib import Path
from storitad_web.ingest import mdfile

SAMPLE = """---
id: 20260101-120000-voice
subject: Hello
tags: [a, b]
---

## Transcript

old transcript

## Notes

old notes
"""

def _write(tmp_path: Path) -> Path:
    md = tmp_path / "e.md"
    md.write_text(SAMPLE)
    return md

def test_load_fm_splits_frontmatter_and_body(tmp_path):
    fm, body = mdfile.load_fm(_write(tmp_path))
    assert fm["id"] == "20260101-120000-voice"
    assert "## Transcript" in body

def test_replace_section_replaces_existing(tmp_path):
    fm, body = mdfile.load_fm(_write(tmp_path))
    out = mdfile.replace_section(body, "Transcript", "new transcript")
    assert "new transcript" in out
    assert "old transcript" not in out
    assert "old notes" in out

def test_replace_section_appends_when_absent(tmp_path):
    out = mdfile.replace_section("## Transcript\n\nx\n", "Notes", "added")
    assert "## Notes" in out and "added" in out

def test_replace_section_drops_when_empty(tmp_path):
    out = mdfile.replace_section("## Transcript\n\nx\n\n## Notes\n\nn\n", "Notes", "")
    assert "## Notes" not in out

def test_write_fm_roundtrips(tmp_path):
    md = _write(tmp_path)
    fm, body = mdfile.load_fm(md)
    fm["subject"] = "Changed"
    mdfile.write_fm(md, fm, body)
    fm2, _ = mdfile.load_fm(md)
    assert fm2["subject"] == "Changed"

def test_find_entry_md_by_basename(tmp_path):
    root = tmp_path / "entries" / "2026" / "01"
    root.mkdir(parents=True)
    (root / "20260101-120000-voice.md").write_text(SAMPLE)
    found = mdfile.find_entry_md(tmp_path / "entries", "20260101-120000-voice")
    assert found is not None and found.name == "20260101-120000-voice.md"
