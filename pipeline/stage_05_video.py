"""Stage 5: assemble the per-scene Ken Burns clips into the final captioned,
watermarked, narrated video."""
import json
from pathlib import Path

import yaml

from pipeline import ffmpeg_utils, status_store
from pipeline.config import CONFIG_DIR, REPO_ROOT


def _resolve_watermark(video_cfg: dict) -> Path | None:
    """Watermark is optional branding — a missing file should never stop a
    video from rendering (it previously crashed every run)."""
    configured = video_cfg.get("watermark_path")
    if not configured:
        return None
    path = REPO_ROOT / configured
    return path if path.exists() else None


def run(video_id: str, out_dir: Path) -> dict:
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))
    durations = json.loads((out_dir / "audio" / "durations.json").read_text(encoding="utf-8"))["durations_seconds"]
    video_cfg = yaml.safe_load((CONFIG_DIR / "video.yaml").read_text(encoding="utf-8"))

    video_dir = out_dir / "video"
    images_dir = out_dir / "images"
    audio_dir = out_dir / "audio"
    scenes = script["scenes"]

    # 1. Per-scene silent Ken Burns clips.
    clip_paths = []
    for i, (scene, duration) in enumerate(zip(scenes, durations), start=1):
        image_path = images_dir / f"scene_{i:02d}.png"
        clip_path = video_dir / f"clip_{i:02d}.mp4"
        cmd = ffmpeg_utils.build_zoompan_cmd(image_path, clip_path, duration, video_cfg)
        ffmpeg_utils.run(cmd)
        clip_paths.append(clip_path)

    # 2. Concat silent clips.
    list_path = video_dir / "concat_list.txt"
    ffmpeg_utils.build_concat_list_file(clip_paths, list_path)
    silent_video_path = video_dir / "silent.mp4"
    ffmpeg_utils.run(ffmpeg_utils.build_video_concat_cmd(list_path, silent_video_path))

    # 3. Concat narration audio via the concat demuxer (see ffmpeg_utils for
    #    why the concat: protocol is unsuitable here).
    audio_paths = [audio_dir / f"scene_{i:02d}.mp3" for i in range(1, len(scenes) + 1)]
    audio_list_path = video_dir / "audio_concat_list.txt"
    ffmpeg_utils.build_concat_list_file(audio_paths, audio_list_path)
    audio_track_path = video_dir / "audio_track.m4a"
    ffmpeg_utils.run(ffmpeg_utils.build_audio_concat_cmd(audio_list_path, audio_track_path))

    # 4. Captions (one block per scene).
    srt_path = video_dir / "captions.srt"
    ffmpeg_utils.build_srt([s["narration_text"] for s in scenes], durations, srt_path)

    # 5. Final mux: captions + optional watermark + audio, encode to delivery codec.
    final_path = video_dir / "final.mp4"
    cmd = ffmpeg_utils.build_final_mux_cmd(
        silent_video_path,
        audio_track_path,
        srt_path,
        final_path,
        video_cfg,
        watermark_path=_resolve_watermark(video_cfg),
    )
    ffmpeg_utils.run(cmd)

    total_duration = sum(durations)
    status_store.update_record(video_id, duration_seconds=round(total_duration, 1))

    return {"final_video_path": str(final_path), "duration_seconds": total_duration}
