#!/usr/bin/env python3
"""Mark a generated video as uploaded to YouTube.

Reads its inputs from the environment rather than accepting them
interpolated into a shell/Python string — workflow inputs are untrusted text
and interpolating them directly into a `python -c` body is a script-injection
vector.

Usage (locally):
    VIDEO_ID=2026-07-27 YOUTUBE_URL=https://youtu.be/xyz python scripts/mark_uploaded.py
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import status_store  # noqa: E402

ALLOWED_URL_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com", "studio.youtube.com"}


def _validate_video_id(video_id: str) -> str:
    video_id = video_id.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", video_id):
        raise SystemExit(f"Invalid video_id {video_id!r}: expected YYYY-MM-DD.")
    try:
        datetime.strptime(video_id, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid video_id {video_id!r}: {exc}") from exc
    return video_id


def _validate_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_URL_HOSTS:
        raise SystemExit(f"Invalid youtube_url {url!r}: expected an https:// YouTube URL.")
    return url


def main() -> None:
    video_id = _validate_video_id(os.environ.get("VIDEO_ID", ""))
    youtube_url = _validate_url(os.environ.get("YOUTUBE_URL", ""))

    if status_store.get_record(video_id) is None:
        raise SystemExit(f"No status record found for {video_id}.")

    status_store.update_record(
        video_id,
        status="uploaded",
        youtube_uploaded=True,
        youtube_url=youtube_url,
    )
    print(f"Marked {video_id} as uploaded: {youtube_url}")


if __name__ == "__main__":
    main()
