"""Runs the seven pipeline stages in order for a given date, updating
docs/data/videos.json before/after each stage so a failure is always
visible on the dashboard instead of the run silently disappearing."""
from datetime import date as date_cls

from pipeline import config, status_store
from pipeline import stage_01_topic, stage_02_script, stage_03_tts
from pipeline import stage_04_images, stage_05_video, stage_06_thumbnail, stage_07_package


def run_pipeline(run_date: date_cls) -> dict:
    video_id = run_date.isoformat()
    out_dir = config.out_dir_for(video_id)

    existing = status_store.get_record(video_id)
    if existing is None:
        status_store.init_record(video_id)
    elif existing["status"] in ("ready_to_download", "uploaded"):
        raise RuntimeError(f"{video_id} already completed (status={existing['status']}); nothing to do")
    else:
        # Prior attempt failed or was interrupted — allow a clean retry.
        status_store.update_record(video_id, status="running", error_message=None)

    # Checked *after* the record exists so a missing-key failure shows up on
    # the dashboard as a failed run rather than vanishing silently.
    try:
        config.require_api_keys()
    except Exception as exc:
        status_store.update_record(video_id, status="failed", error_message=str(exc))
        raise

    def _stage(name: str, fn, *args, **kwargs):
        status_store.start_stage(video_id, name)
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - top-level stage boundary, must not crash the workflow
            status_store.finish_stage(video_id, name, error=f"{type(exc).__name__}: {exc}")
            raise
        status_store.finish_stage(video_id, name)
        return result

    _stage("topic", stage_01_topic.run, video_id, run_date, out_dir)
    _stage("script", stage_02_script.run, video_id, out_dir)
    _stage("tts", stage_03_tts.run, video_id, out_dir)
    _stage("images", stage_04_images.run, video_id, out_dir)
    _stage("video", stage_05_video.run, video_id, out_dir)
    _stage("thumbnail", stage_06_thumbnail.run, video_id, out_dir)
    package_result = _stage("package", stage_07_package.run, video_id, out_dir)

    return {"video_id": video_id, "out_dir": str(out_dir), **package_result}
