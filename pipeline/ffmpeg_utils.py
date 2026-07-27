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
from typing import Optional


class FFmpegError(RuntimeError):
    """Raised with ffmpeg's stderr attached — the bare CalledProcessError
    message omits it, which makes unattended failures undebuggable."""


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()[-15:]
        raise FFmpegError(
            f"ffmpeg failed (exit {result.returncode}): {' '.join(cmd[:6])} ...\n" + "\n".join(tail)
        )


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
    """Concat-demuxer manifest. Single quotes in paths are escaped per
    ffmpeg's concat syntax."""
    lines = [f"file '{str(p.resolve()).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'" for p in clip_paths]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return list_path


def build_video_concat_cmd(list_path: Path, out_path: Path) -> list[str]:
    return [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c", "copy",
        str(out_path),
    ]


def build_audio_concat_cmd(list_path: Path, out_path: Path) -> list[str]:
    """Uses the concat *demuxer* with a re-encode.

    The `concat:` protocol byte-joins MP3 files including their ID3 headers,
    which introduces small per-file offsets that accumulate across ~10 scenes
    and drift narration out of sync with the captions and Ken Burns clips.
    Decoding and re-encoding through the demuxer produces one correctly
    timed stream.
    """
    return [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:a", "aac", "-b:a", "192k",
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
    out_path: Path,
    cfg: dict,
    watermark_path: Optional[Path] = None,
) -> list[str]:
    """One pass: burn in captions, optionally overlay a watermark, mux the
    narration audio, and encode to the final delivery codec.

    `watermark_path` is optional — a missing branding asset should not stop
    a video from rendering.
    """
    subtitles_filter = (
        f"subtitles={_escape_ffmpeg_path(srt_path)}:"
        f"force_style='FontSize={cfg['caption_font_size']},"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
        f"Outline=2,MarginV={cfg['caption_margin_v']}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(silent_video_path),
        "-i", str(audio_track_path),
    ]

    if watermark_path is not None:
        margin = cfg["watermark_margin_px"]
        cmd += ["-i", str(watermark_path)]
        filter_complex = (
            f"[0:v]{subtitles_filter}[v1];"
            f"[v1][2:v]overlay=W-w-{margin}:H-h-{margin}[vout]"
        )
    else:
        filter_complex = f"[0:v]{subtitles_filter}[vout]"

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "1:a",
        # CRF alone controls quality; specifying a target bitrate too would
        # conflict and be silently ignored.
        "-c:v", cfg["video_codec"], "-crf", str(cfg["crf"]),
        "-pix_fmt", "yuv420p",
        "-c:a", cfg["audio_codec"],
        "-shortest",
        str(out_path),
    ]
    return cmd


def _escape_ffmpeg_path(path: Path) -> str:
    # ffmpeg filter arguments treat ':' and '\' specially; escape for the
    # subtitles filter's path argument.
    return str(path).replace("\\", "\\\\").replace(":", "\\:")
