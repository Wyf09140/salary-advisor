import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("SA_RAW", ROOT / "data" / "raw"))  # override for tests
PROCESSED = Path(os.environ.get("SA_PROCESSED", ROOT / "data" / "processed"))
MODELS = ROOT / "models"
CONFIG = ROOT / "config"


def load(name: str) -> dict:
    with open(CONFIG / f"{name}.yaml") as f:
        return yaml.safe_load(f)


SOURCES = load("sources")
SOC_CODES = set(load("soc_codes")["soc_codes"])
SKILLS = load("skills")["skills"]
