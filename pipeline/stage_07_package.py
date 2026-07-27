"""Stage 7: package outputs for delivery — commit a small preview thumbnail
to the dashboard, write the upload metadata, and mark the video
ready_to_download in the status store."""
import json
import shutil
from pathlib import Path

from pipeline import costs, status_store
from pipeline.config import DOCS_DIR

UPLOAD_CHECKLIST = """UPLOAD CHECKLIST — read before publishing
=========================================

[ ] Set "Made for Kids" = YES in the YouTube upload flow.
    This is a legal requirement (COPPA), not a preference. Misdeclaring
    children's content carries FTC penalties per violation. It disables
    personalised ads and comments on this video — that is expected.

[ ] Watch the video start to finish before publishing. You are the only
    human review step in this pipeline. Check specifically for:
      - the mascot looking consistent and not resembling any existing
        character you recognise from a film, show, book, or game
      - narration matching the captions (audio drift)
      - anything a parent would find inappropriate or frightening

[ ] Confirm the title/description contain no brand or character names.

Title:       {title}
Theme:       {theme}
Moral:       {moral}
Duration:    {duration}
Est. cost:   ${cost}
"""


def run(video_id: str, out_dir: Path) -> dict:
    topic = json.loads((out_dir / "topic.json").read_text(encoding="utf-8"))
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))

    # Small committed preview thumbnail for the dashboard.
    dashboard_thumb_dir = DOCS_DIR / "videos" / video_id
    dashboard_thumb_dir.mkdir(parents=True, exist_ok=True)
    dashboard_thumb_path = dashboard_thumb_dir / "thumb.jpg"
    shutil.copy(out_dir / "thumbnail" / "thumb.jpg", dashboard_thumb_path)

    # Metadata bundled alongside the video artifact for manual upload.
    (out_dir / "description.txt").write_text(script["video_description"], encoding="utf-8")
    (out_dir / "tags.txt").write_text(", ".join(script["tags"]), encoding="utf-8")

    record = status_store.get_record(video_id) or {}
    cost = costs.total_usd(out_dir)
    duration = record.get("duration_seconds")

    (out_dir / "UPLOAD_CHECKLIST.txt").write_text(
        UPLOAD_CHECKLIST.format(
            title=topic["title"],
            theme=topic.get("theme_category", "—"),
            moral=topic["moral"],
            duration=f"{duration}s" if duration else "—",
            cost=cost,
        ),
        encoding="utf-8",
    )

    thumbnail_rel_path = f"videos/{video_id}/thumb.jpg"
    status_store.update_record(
        video_id,
        status="ready_to_download",
        current_stage="done",
        thumbnail_path=thumbnail_rel_path,
        cost_estimate_usd=cost,
    )

    return {"thumbnail_path": thumbnail_rel_path, "cost_estimate_usd": cost}
