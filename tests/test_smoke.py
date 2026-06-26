def test_vendored_modules_import():
    from storitad_web.ingest import sidecar, transcribe, render_markdown, normalise
    assert hasattr(sidecar, "load")
    assert hasattr(render_markdown, "write_entry")
    assert hasattr(transcribe, "transcribe")
    assert hasattr(normalise, "normalise_to")
