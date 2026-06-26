"""Vendored from the storitad repo's ingest/storitad_ingest/ package.

These modules (sidecar, transcribe, render_markdown, normalise) are a
snapshot copied in so this webapp is a self-contained deployable with no
cross-repo dependency. They are lightly adapted here — `mdfile` is added
and `render_markdown` gains an `author` field — so do not blindly
re-sync from upstream; reconcile changes deliberately.
"""
