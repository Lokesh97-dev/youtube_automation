"""Stage 2: expand the approved topic into a scene-by-scene rhyming
narration script."""
import json
from pathlib import Path

from pipeline import character_bible, llm_client, status_store


def _system_prompt(mascot_name: str) -> str:
    return f"""You write scene-by-scene scripts for a children's YouTube
channel of short narrated (spoken aloud, NOT sung) rhyming stories for ages
3-6, featuring a bunny mascot named {mascot_name}. Narration should rhyme in
simple AABB or ABAB couplets, use short simple sentences, and read naturally
when spoken by a single narrator (not a song). Keep vocabulary appropriate
for preschoolers.

All content must be original. Do not reference or paraphrase existing
published stories, songs, characters, or brands."""


def run(video_id: str, out_dir: Path) -> dict:
    topic = json.loads((out_dir / "topic.json").read_text(encoding="utf-8"))
    bible = character_bible.load()

    user_prompt = f"""Title: {topic['title']}
Premise: {topic['premise']}
Moral: {topic['moral']}
Target scene count: {topic['scene_count_target']}

Write the full script as a JSON object with exactly these keys:
- "scenes": an array of {topic['scene_count_target']} objects, each with:
    - "narration_text": the rhyming narration for this scene (1-3 sentences)
    - "visual_description": a concrete visual description of what's happening
      in this scene for an illustrator (setting, action, mood — do not
      re-describe {bible['name']}'s appearance, only the scene/action)
    - "estimated_duration_seconds": rough estimate of spoken duration
- "video_description": a 2-3 sentence YouTube video description for this story
- "tags": an array of 8-12 relevant YouTube tags (strings)
"""

    result = llm_client.generate_json(
        _system_prompt(bible["name"]), user_prompt, max_tokens=3000, out_dir=out_dir
    )

    _validate(result)

    (out_dir / "script.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    word_count = sum(len(s["narration_text"].split()) for s in result["scenes"])
    status_store.update_record(
        video_id,
        scene_count=len(result["scenes"]),
        word_count=word_count,
    )
    return result


def _validate(script: dict) -> None:
    """Fail here with a clear message rather than several stages later with a
    KeyError or an empty video."""
    if not script.get("scenes"):
        raise ValueError("Script contains no scenes")
    for i, scene in enumerate(script["scenes"], start=1):
        for key in ("narration_text", "visual_description"):
            if not scene.get(key):
                raise ValueError(f"Scene {i} is missing '{key}'")
    if not script.get("video_description"):
        raise ValueError("Script is missing 'video_description'")
    if not script.get("tags"):
        raise ValueError("Script is missing 'tags'")
