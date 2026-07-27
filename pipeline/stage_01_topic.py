"""Stage 1: pick today's theme category and generate a fresh, non-repeating
story premise via Claude."""
import json
from datetime import date as date_cls
from pathlib import Path

from pipeline import character_bible, llm_client, status_store, topics_bank


def _system_prompt(mascot_name: str) -> str:
    # Built from the character bible so renaming the mascot is a config-only
    # change and can never drift out of sync with the image prompts.
    return f"""You write original premises for a children's YouTube channel
of short narrated (spoken, not sung) rhyming stories for ages 3-6, featuring
a recurring bunny mascot named {mascot_name}. Each story teaches one simple
lesson tied to the given theme category. Premises must be wholesome,
non-scary, and never repeat a plot, setting, or moral already used.

The premise must be entirely original. Do not adapt, retell, or borrow
characters, settings, or plots from existing books, films, television shows,
or other published stories."""


def run(video_id: str, run_date: date_cls, out_dir: Path) -> dict:
    category = topics_bank.pick_category(run_date)
    history = topics_bank.get_recent_history()
    bible = character_bible.load()
    max_retries = topics_bank.load().get("max_duplicate_retries", 3)

    history_block = "\n".join(f"- {h['title']}: {h.get('premise', '')}" for h in history) or "(none yet)"

    user_prompt = f"""Mascot: {bible['name']} — {bible['description'].strip()}

Today's theme category: {category['label']} ({category['prompt_hint']})

Titles/premises already used — do NOT repeat these plots, settings, or morals:
{history_block}

Return a JSON object with exactly these keys:
- "title": a short catchy video title (max 70 chars)
- "premise": 2-3 sentences describing the story
- "moral": the one-sentence lesson the story teaches
- "scene_count_target": an integer between 8 and 12
"""

    result = None
    rejected: list[str] = []
    for _ in range(max_retries):
        candidate = llm_client.generate_json(
            _system_prompt(bible["name"]), user_prompt, max_tokens=600, out_dir=out_dir
        )
        if not topics_bank.is_near_duplicate(candidate["title"], candidate["premise"], history):
            result = candidate
            break
        rejected.append(candidate["title"])
        user_prompt += (
            f"\n\nYour previous attempt \"{candidate['title']}\" was too similar to an existing "
            "story. Try a genuinely different plot, setting, and cast of side characters."
        )

    if result is None:
        raise RuntimeError(
            f"Could not generate a non-duplicate topic for {video_id} after {max_retries} attempts "
            f"(rejected: {rejected}). The topic bank may need more categories."
        )

    result["theme_category"] = category["id"]
    (out_dir / "topic.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    status_store.update_record(
        video_id,
        theme_category=category["id"],
        title=result["title"],
        premise=result["premise"],
        moral=result["moral"],
    )
    return result
