"""Environment/secret loading and shared path constants."""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")  # no-op if the file doesn't exist (e.g. in CI, which uses real secrets)
CONFIG_DIR = REPO_ROOT / "config"
ASSETS_DIR = REPO_ROOT / "assets"
DOCS_DIR = REPO_ROOT / "docs"
DATA_FILE = DOCS_DIR / "data" / "videos.json"
OUT_DIR = REPO_ROOT / "out"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_TTS_API_KEY = os.environ.get("GOOGLE_TTS_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Haiku keeps cost per video low; override via env if you want higher-quality
# prose and don't mind the added cost.
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def require_api_keys() -> None:
    missing = [
        name
        for name, value in [
            ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
            ("GOOGLE_TTS_API_KEY", GOOGLE_TTS_API_KEY),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def out_dir_for(date_str: str) -> Path:
    d = OUT_DIR / date_str
    (d / "audio").mkdir(parents=True, exist_ok=True)
    (d / "images").mkdir(parents=True, exist_ok=True)
    (d / "video").mkdir(parents=True, exist_ok=True)
    (d / "thumbnail").mkdir(parents=True, exist_ok=True)
    return d
