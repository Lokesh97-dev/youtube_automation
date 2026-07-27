"""Validation tests for scripts/mark_uploaded.py.

These matter because the values come from a workflow_dispatch form — the
previous implementation interpolated them straight into a `python -c` body,
which was a script-injection vector.
"""
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("mark_uploaded", REPO_ROOT / "scripts" / "mark_uploaded.py")
mark_uploaded = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mark_uploaded)


@pytest.mark.parametrize("value", ["2026-07-27", "2026-01-01", "2026-12-31"])
def test_valid_video_ids_accepted(value):
    assert mark_uploaded._validate_video_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-a-date",
        "2026-13-01",          # month out of range
        "2026-02-30",          # day out of range for the month
        "2026-07-27; rm -rf /",  # injection attempt
        "2026-07-27')\nimport os",
    ],
)
def test_invalid_video_ids_rejected(value):
    with pytest.raises(SystemExit):
        mark_uploaded._validate_video_id(value)


@pytest.mark.parametrize(
    "value",
    [
        "https://youtu.be/abc123",
        "https://www.youtube.com/watch?v=abc123",
        "https://youtube.com/watch?v=abc123",
    ],
)
def test_valid_youtube_urls_accepted(value):
    assert mark_uploaded._validate_url(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "http://youtu.be/abc",              # non-https
        "https://evil.example.com/abc",     # wrong host
        "javascript:alert(1)",              # scheme injection
        "https://youtube.com.evil.test/x",  # lookalike host
    ],
)
def test_invalid_urls_rejected(value):
    with pytest.raises(SystemExit):
        mark_uploaded._validate_url(value)
