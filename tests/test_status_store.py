import pytest

from pipeline import status_store


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    data_file = tmp_path / "videos.json"
    monkeypatch.setattr(status_store, "DATA_FILE", data_file)
    return data_file


def test_load_all_returns_empty_list_when_file_missing(tmp_store):
    assert status_store.load_all() == []


def test_init_record_creates_expected_shape(tmp_store):
    record = status_store.init_record("2026-07-27")
    assert record["id"] == "2026-07-27"
    assert record["status"] == "running"
    assert record["current_stage"] == "topic"
    assert set(record["stages"].keys()) == set(status_store.STAGES)
    assert status_store.get_record("2026-07-27") is not None


def test_init_record_rejects_duplicate_id(tmp_store):
    status_store.init_record("2026-07-27")
    with pytest.raises(ValueError):
        status_store.init_record("2026-07-27")


def test_start_and_finish_stage_success(tmp_store):
    status_store.init_record("2026-07-27")
    status_store.start_stage("2026-07-27", "topic")
    record = status_store.get_record("2026-07-27")
    assert record["stages"]["topic"]["status"] == "running"

    status_store.finish_stage("2026-07-27", "topic")
    record = status_store.get_record("2026-07-27")
    assert record["stages"]["topic"]["status"] == "success"
    assert record["status"] == "running"  # overall status untouched on success


def test_finish_stage_with_error_marks_record_failed(tmp_store):
    status_store.init_record("2026-07-27")
    status_store.start_stage("2026-07-27", "script")
    status_store.finish_stage("2026-07-27", "script", error="boom")

    record = status_store.get_record("2026-07-27")
    assert record["stages"]["script"]["status"] == "failed"
    assert record["status"] == "failed"
    assert record["error_message"] == "boom"


def test_update_record_merges_fields(tmp_store):
    status_store.init_record("2026-07-27")
    status_store.update_record("2026-07-27", title="Hoplin Shares", scene_count=9)
    record = status_store.get_record("2026-07-27")
    assert record["title"] == "Hoplin Shares"
    assert record["scene_count"] == 9


def test_recent_titles_returns_newest_first_within_window(tmp_store):
    status_store.init_record("2026-07-25")
    status_store.update_record("2026-07-25", title="Old Story", premise="p1")
    status_store.init_record("2026-07-27")
    status_store.update_record("2026-07-27", title="New Story", premise="p2")

    titles = status_store.recent_titles(window=10)
    assert [t["title"] for t in titles] == ["New Story", "Old Story"]
