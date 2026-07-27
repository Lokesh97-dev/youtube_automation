"""ffmpeg/ffprobe helpers: Ken Burns pan/zoom clips, concat, caption burn-in,
audio mux, watermark overlay. Calls the ffmpeg/ffprobe binaries directly via
subprocess (both are preinstalled on GitHub Actions Ubuntu runners) rather
than a Python video-editing dependency.

Command-building functions are pure (return an argv list, do not execute)
so they can be unit tested without ffmpeg installed. `run()` is the only
function that actually shells out.
"""
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def get_audio_duration_seconds(audio_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def build_zoompan_cmd(image_path: Path, out_path: Path, duration_seconds: float, cfg: dict) -> list[str]:
    """Ken Burns pan/zoom: slow linear zoom from zoom_start to zoom_end over
    the clip's duration, scaled to the target resolution."""
    fps = cfg["fps"]
    width = cfg["width"]
    height = cfg["height"]
    zoom_start = cfg["ken_burns_zoom_start"]
    zoom_end = cfg["ken_burns_zoom_end"]
    total_frames = max(int(round(duration_seconds * fps)), 1)
    zoom_step = (zoom_end - zoom_start) / total_frames
    zoom_expr = f"min(zoom+{zoom_step:.6f},{zoom_end})"
    filter_str = (
        f"scale={width * 2}:{height * 2},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:s={width}x{height}:fps={fps}"
    )
    return [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", filter_str,
        "-t", f"{duration_seconds:.3f}",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]


def build_concat_list_file(clip_paths: list[Path], list_path: Path) -> Path:
    lines = [f"file '{p.resolve()}'" for p in clip_paths]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return list_path


def build_video_concat_cmd(list_path: Path, out_path: Path) -> list[str]:
    return [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c", "copy",
        str(out_path),
    ]


def build_audio_concat_cmd(audio_paths: list[Path], out_path: Path) -> list[str]:
    concat_input = "concat:" + "|".join(str(p) for p in audio_paths)
    return [
        "ffmpeg", "-y",
        "-i", concat_input,
        "-acodec", "aac",
        str(out_path),
    ]


def format_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(scene_texts: list[str], scene_durations: list[float], out_path: Path) -> Path:
    lines = []
    cursor = 0.0
    for i, (text, duration) in enumerate(zip(scene_texts, scene_durations), start=1):
        start = format_srt_timestamp(cursor)
        end = format_srt_timestamp(cursor + duration)
        lines.append(f"{i}\n{start} --> {end}\n{text.strip()}\n")
        cursor += duration
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def build_final_mux_cmd(
    silent_video_path: Path,
    audio_track_path: Path,
    srt_path: Path,
    watermark_path: Path,
    out_path: Path,
    cfg: dict,
) -> list[str]:
    """One pass: burn in captions, overlay watermark, mux narration audio,
    encode to the final delivery codec/bitrate."""
    margin = cfg["watermark_margin_px"]
    filter_complex = (
        f"[0:v]subtitles={_escape_ffmpeg_path(srt_path)}:"
        f"force_style='FontSize={cfg['caption_font_size']},"
        f"PrimaryColour=&Hffffff,OutlineColour=&H000000,MarginV={cfg['caption_margin_v']}'[v1];"
        f"[v1][2:v]overlay=W-w-{margin}:H-h-{margin}[vout]"
    )
    return [
        "ffmpeg", "-y",
        "-i", str(silent_video_path),
        "-i", str(audio_track_path),
        "-i", str(watermark_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "1:a",
        "-c:v", cfg["video_codec"], "-b:v", cfg["video_bitrate"], "-crf", str(cfg["crf"]),
        "-c:a", cfg["audio_codec"],
        "-shortest",
        str(out_path),
    ]


def _escape_ffmpeg_path(path: Path) -> str:
    # ffmpeg filter arguments treat ':' and '\' specially; escape for the
    # subtitles filter's path argument.
    return str(path).replace("\\", "\\\\").replace(":", "\\:")
