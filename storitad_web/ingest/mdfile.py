# storitad_web/ingest/mdfile.py
"""Shared helpers for reading/rewriting entry markdown (frontmatter + sections)."""
from __future__ import annotations

from pathlib import Path

import yaml


def load_fm(md: Path) -> tuple[dict, str]:
    text = md.read_text()
    if not text.startswith("---"):
        return {}, text
    _, fm_block, body = text.split("---", 2)
    return yaml.safe_load(fm_block) or {}, body


def write_fm(md: Path, fm: dict, body: str) -> None:
    md.write_text(
        "---\n"
        + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).rstrip()
        + "\n---\n\n"
        + body.lstrip("\n")
        + ("\n" if not body.endswith("\n") else "")
    )


def find_entry_md(entries_root: Path, entry_id: str) -> Path | None:
    for candidate in entries_root.rglob(f"{entry_id}.md"):
        return candidate
    for md in entries_root.rglob("*.md"):
        text = md.read_text()
        if not text.startswith("---"):
            continue
        try:
            _, fm, _ = text.split("---", 2)
            if (yaml.safe_load(fm) or {}).get("id") == entry_id:
                return md
        except (ValueError, yaml.YAMLError):
            continue
    return None


def replace_section(body: str, heading: str, content: str) -> str:
    """Replace the `## <heading>` section. Empty content drops it; a missing
    section with non-empty content appends one."""
    target = f"## {heading}".lower()
    lines = body.splitlines()
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.strip().lower() == target:
            start = i
        elif start is not None and line.startswith("## "):
            end = i
            break
    content = content.strip()
    if start is None:
        if not content:
            return body
        sep = "" if body.endswith("\n\n") else ("\n" if body.endswith("\n") else "\n\n")
        return body + f"{sep}## {heading}\n\n{content}\n"
    if not content:
        new = lines[:start] + lines[end:]
    else:
        new = lines[:start] + [f"## {heading}", "", content, ""] + lines[end:]
    return "\n".join(new).rstrip() + "\n"
