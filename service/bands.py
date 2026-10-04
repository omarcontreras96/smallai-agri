"""Load the band file from workstream A (models/bands.json), falling back to the sample."""
import json
import os
from pathlib import Path

MODELS = Path(__file__).resolve().parent.parent / "models"


def bands_path() -> Path:
    if os.environ.get("BANDS_PATH"):
        return Path(os.environ["BANDS_PATH"])
    real = MODELS / "bands.json"
    return real if real.exists() else MODELS / "bands.sample.json"


def load_bands(path: Path | None = None) -> dict:
    with open(path or bands_path(), encoding="utf-8") as f:
        return json.load(f)
