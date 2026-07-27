"""Stage 7: package outputs for delivery — commit a small preview thumbnail
to the dashboard, write description/tags for the user's manual upload, and
mark the video ready_to_download in the status store."""
import json
import shutil
from pathlib import Path

from pipeline import status_store
from pipeline.config import DOCS_DIR

# Rough per-video cost estimate (see plan doc §8) for dashboard visibility.
COST_ESTIMATE_USD = 0.65


def run(video_id: str, out_dir: Path) -> dict:
    topic = json.loads((out_dir / "topic.json").read_text(encoding="utf-8"))
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))

    # Small committed preview thumbnail for the dashboard.
    dashboard_thumb_dir = DOCS_DIR / "videos" / video_id
    dashboard_thumb_dir.mkdir(parents=True, exist_ok=True)
    dashboard_thumb_path = dashboard_thumb_dir / "thumb.jpg"
    shutil.copy(out_dir / "thumbnail" / "thumb.jpg", dashboard_thumb_path)

    # Description/tags bundled alongside the video artifact for manual upload.
    (out_dir / "description.txt").write_text(script["video_description"], encoding="utf-8")
    (out_dir / "tags.txt").write_text(", ".join(script["tags"]), encoding="utf-8")

    thumbnail_rel_path = f"videos/{video_id}/thumb.jpg"
    status_store.update_record(
        video_id,
        status="ready_to_download",
        current_stage="done",
        thumbnail_path=thumbnail_rel_path,
        cost_estimate_usd=COST_ESTIMATE_USD,
    )

    return {"thumbnail_path": thumbnail_rel_path}
