"""Stage 2: expand the approved topic into a scene-by-scene rhyming
narration script."""
import json
from pathlib import Path

from pipeline import llm_client, status_store

SYSTEM_PROMPT = """You write scene-by-scene scripts for a children's YouTube
channel of short narrated (spoken aloud, NOT sung) rhyming stories for ages
3-6, featuring a bunny mascot named Rhymo. Narration should rhyme in simple
AABB or ABAB couplets, use short simple sentences, and read naturally when
spoken by a single narrator (not a song). Keep vocabulary appropriate for
preschoolers."""


def run(video_id: str, out_dir: Path) -> dict:
    topic = json.loads((out_dir / "topic.json").read_text(encoding="utf-8"))

    user_prompt = f"""Title: {topic['title']}
Premise: {topic['premise']}
Moral: {topic['moral']}
Target scene count: {topic['scene_count_target']}

Write the full script as a JSON object with exactly these keys:
- "scenes": an array of {topic['scene_count_target']} objects, each with:
    - "narration_text": the rhyming narration for this scene (1-3 sentences)
    - "visual_description": a concrete visual description of what's happening
      in this scene for an illustrator (setting, action, mood — do not
      re-describe Rhymo's appearance, only the scene/action)
    - "estimated_duration_seconds": rough estimate of spoken duration
- "video_description": a 2-3 sentence YouTube video description for this story
- "tags": an array of 8-12 relevant YouTube tags (strings)
"""

    result = llm_client.generate_json(SYSTEM_PROMPT, user_prompt, max_tokens=3000)

    (out_dir / "script.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    word_count = sum(len(s["narration_text"].split()) for s in result["scenes"])
    status_store.update_record(
        video_id,
        scene_count=len(result["scenes"]),
        word_count=word_count,
    )
    return result
