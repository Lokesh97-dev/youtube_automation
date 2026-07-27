"""Stage 1: pick today's theme category and generate a fresh, non-repeating
story premise via Claude."""
import json
from datetime import date as date_cls
from pathlib import Path

from pipeline import llm_client, topics_bank, character_bible, status_store

SYSTEM_PROMPT = """You write original premises for a children's YouTube channel
of short narrated (spoken, not sung) rhyming stories for ages 3-6, featuring
a recurring bunny mascot named Rhymo. Each story teaches one simple lesson
tied to the given theme category. Premises must be wholesome, non-scary, and
never repeat a plot, setting, or moral already used."""


def run(video_id: str, run_date: date_cls, out_dir: Path) -> dict:
    category = topics_bank.pick_category(run_date)
    history = topics_bank.get_recent_history()
    bible = character_bible.load()

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
    for attempt in range(2):
        candidate = llm_client.generate_json(SYSTEM_PROMPT, user_prompt, max_tokens=600)
        if not topics_bank.is_near_duplicate(candidate["title"], candidate["premise"], history):
            result = candidate
            break
        user_prompt += f"\n\nYour previous attempt \"{candidate['title']}\" was too similar to an existing story. Try a genuinely different plot and setting."
    if result is None:
        raise RuntimeError(f"Could not generate a non-duplicate topic for {video_id} after retry")

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
