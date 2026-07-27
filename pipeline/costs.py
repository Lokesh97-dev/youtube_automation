"""Per-run API cost accumulation.

The dashboard previously displayed a hardcoded guess, which is worse than
showing nothing — it looks like measured data. Each stage now records what it
actually consumed into out/<date>/costs.json, and stage 7 sums it.

RATES are list prices at the time of writing and are the one thing here that
goes stale. Check them against the providers' pricing pages periodically;
they are deliberately in one place so updating is a one-line change.
"""
import json
from pathlib import Path

COSTS_FILENAME = "costs.json"

RATES = {
    # Anthropic, per million tokens (claude-haiku-4-5).
    "claude_input_per_mtok": 1.00,
    "claude_output_per_mtok": 5.00,
    # Google Cloud TTS Neural2, per million characters.
    "tts_neural2_per_mchar": 16.00,
    # OpenAI gpt-image-1, per generated image by quality tier.
    "image_low": 0.011,
    "image_medium": 0.042,
    "image_high": 0.167,
}


def _path(out_dir: Path) -> Path:
    return out_dir / COSTS_FILENAME


def _load(out_dir: Path) -> dict:
    p = _path(out_dir)
    if not p.exists():
        return {"llm_input_tokens": 0, "llm_output_tokens": 0, "tts_characters": 0, "images": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def _save(out_dir: Path, data: dict) -> None:
    _path(out_dir).write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_llm(out_dir: Path, input_tokens: int, output_tokens: int) -> None:
    data = _load(out_dir)
    data["llm_input_tokens"] += input_tokens
    data["llm_output_tokens"] += output_tokens
    _save(out_dir, data)


def record_tts(out_dir: Path, characters: int) -> None:
    data = _load(out_dir)
    data["tts_characters"] += characters
    _save(out_dir, data)


def record_image(out_dir: Path, quality: str) -> None:
    data = _load(out_dir)
    data["images"][quality] = data["images"].get(quality, 0) + 1
    _save(out_dir, data)


def total_usd(out_dir: Path) -> float:
    data = _load(out_dir)
    total = (
        data["llm_input_tokens"] / 1_000_000 * RATES["claude_input_per_mtok"]
        + data["llm_output_tokens"] / 1_000_000 * RATES["claude_output_per_mtok"]
        + data["tts_characters"] / 1_000_000 * RATES["tts_neural2_per_mchar"]
    )
    for quality, count in data["images"].items():
        total += count * RATES.get(f"image_{quality}", RATES["image_medium"])
    return round(total, 4)
