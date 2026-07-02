from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "storitad_web" / "static"


def test_vendored_model_and_wasm_present():
    assert (STATIC / "vendor/mediapipe/tasks-vision.mjs").is_file()
    assert (STATIC / "vendor/mediapipe/selfie_segmenter.tflite").is_file()
    wasm = STATIC / "vendor/mediapipe/wasm"
    assert (wasm / "vision_wasm_internal.js").is_file()
    assert (wasm / "vision_wasm_internal.wasm").is_file()


def test_background_placeholders_present():
    assert (STATIC / "backgrounds/office.svg").is_file()
    assert (STATIC / "backgrounds/bookshelf.svg").is_file()


def test_package_data_covers_new_dirs():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    globs = data["tool"]["setuptools"]["package-data"]["storitad_web"]
    assert "static/backgrounds/*" in globs
    assert "static/vendor/mediapipe/*" in globs
    assert "static/vendor/mediapipe/wasm/*" in globs
