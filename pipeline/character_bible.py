"""Loads config/character_bible.yaml into prompt fragments used by
every image-generation call, so the mascot's appearance never drifts."""
from functools import lru_cache

import yaml

from pipeline.config import CONFIG_DIR, REPO_ROOT


@lru_cache(maxsize=1)
def load() -> dict:
    with open(CONFIG_DIR / "character_bible.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_image_prompt(scene_visual_description: str) -> str:
    bible = load()
    return (
        f"{bible['style_prefix']}"
        f"Character reference: {bible['description'].strip()} "
        f"Scene: {scene_visual_description.strip()} "
        f"{bible['style_suffix'].strip()} "
        f"Avoid: {'; '.join(bible['negative_constraints'])}."
    )


def reference_image_path():
    bible = load()
    path = REPO_ROOT / bible["reference_image"]
    return path if path.exists() else None
