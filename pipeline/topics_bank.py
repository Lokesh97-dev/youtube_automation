"""Theme rotation + anti-repetition de-dup against status history."""
import difflib
from datetime import date as date_cls
from functools import lru_cache

import yaml

from pipeline.config import CONFIG_DIR
from pipeline import status_store


@lru_cache(maxsize=1)
def load() -> dict:
    with open(CONFIG_DIR / "topics.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def pick_category(run_date: date_cls) -> dict:
    """Deterministic day-of-year rotation so lesson type varies systematically
    rather than depending on LLM randomness."""
    categories = load()["categories"]
    idx = run_date.timetuple().tm_yday % len(categories)
    return categories[idx]


def get_recent_history() -> list[dict]:
    window = load().get("recent_history_window", 30)
    return status_store.recent_titles(window)


def is_near_duplicate(title: str, premise: str, history: list[dict]) -> bool:
    threshold = load().get("similarity_reject_threshold", 0.82)
    candidate = f"{title} {premise}".lower()
    for item in history:
        existing = f"{item['title']} {item.get('premise') or ''}".lower()
        ratio = difflib.SequenceMatcher(None, candidate, existing).ratio()
        if ratio >= threshold:
            return True
    return False
