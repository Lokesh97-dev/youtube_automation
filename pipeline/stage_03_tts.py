"""Stage 3: synthesize narration audio per scene and measure real durations
(which override the LLM's estimate for accurate video pacing)."""
import json
from pathlib import Path

from pipeline import costs, ffmpeg_utils, tts_client


def run(video_id: str, out_dir: Path) -> dict:
    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))
    audio_dir = out_dir / "audio"

    durations = []
    for i, scene in enumerate(script["scenes"], start=1):
        audio_path = audio_dir / f"scene_{i:02d}.mp3"
        text = scene["narration_text"]
        tts_client.synthesize(text, audio_path)
        costs.record_tts(out_dir, len(text))
        duration = ffmpeg_utils.get_audio_duration_seconds(audio_path)
        durations.append(duration)

    result = {"durations_seconds": durations, "total_seconds": sum(durations)}
    (audio_dir / "durations.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
