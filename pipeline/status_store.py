"""Read/write docs/data/videos.json — the single source of truth for
pipeline + dashboard status. One JSON array, one record per video (per day).
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pipeline.config import DATA_FILE

STAGES = ["topic", "script", "tts", "images", "video", "thumbnail", "package"]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_all() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return json.loads(content) if content else []


def save_all(records: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(DATA_FILE.parent), prefix=".videos_", suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, DATA_FILE)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def get_record(video_id: str) -> Optional[dict]:
    for r in load_all():
        if r["id"] == video_id:
            return r
    return None


def init_record(video_id: str) -> dict:
    records = load_all()
    if any(r["id"] == video_id for r in records):
        raise ValueError(f"Record {video_id} already exists")
    record = {
        "id": video_id,
        "run_date": video_id,
        "created_at": _now(),
        "updated_at": _now(),
        "status": "running",
        "current_stage": STAGES[0],
        "stages": {s: {"status": "pending", "started_at": None, "finished_at": None, "error": None} for s in STAGES},
        "theme_category": None,
        "title": None,
        "premise": None,
        "moral": None,
        "scene_count": None,
        "word_count": None,
        "duration_seconds": None,
        "thumbnail_path": None,
        "workflow_run_url": os.environ.get("WORKFLOW_RUN_URL"),
        "artifact_name": f"video-{video_id}",
        "youtube_uploaded": False,
        "youtube_url": None,
        "error_message": None,
        "cost_estimate_usd": 0.0,
    }
    records.append(record)
    save_all(records)
    return record


def update_record(video_id: str, **fields) -> dict:
    records = load_all()
    for r in records:
        if r["id"] == video_id:
            r.update(fields)
            r["updated_at"] = _now()
            save_all(records)
            return r
    raise ValueError(f"Record {video_id} not found")


def start_stage(video_id: str, stage: str) -> None:
    records = load_all()
    for r in records:
        if r["id"] == video_id:
            r["current_stage"] = stage
            r["stages"][stage]["status"] = "running"
            r["stages"][stage]["started_at"] = _now()
            r["updated_at"] = _now()
            save_all(records)
            return
    raise ValueError(f"Record {video_id} not found")


def finish_stage(video_id: str, stage: str, error: Optional[str] = None) -> None:
    records = load_all()
    for r in records:
        if r["id"] == video_id:
            r["stages"][stage]["status"] = "failed" if error else "success"
            r["stages"][stage]["finished_at"] = _now()
            r["stages"][stage]["error"] = error
            r["updated_at"] = _now()
            if error:
                r["status"] = "failed"
                r["error_message"] = error
            save_all(records)
            return
    raise ValueError(f"Record {video_id} not found")


def recent_titles(window: int) -> list[dict]:
    records = sorted(load_all(), key=lambda r: r["run_date"], reverse=True)
    out = []
    for r in records[:window]:
        if r.get("title"):
            out.append({"title": r["title"], "premise": r.get("premise"), "moral": r.get("moral")})
    return out
