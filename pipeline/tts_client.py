"""Google Cloud Text-to-Speech wrapper (REST, API-key auth, Neural2 voices)."""
import base64
from pathlib import Path

import requests
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from pipeline.config import CONFIG_DIR, GOOGLE_TTS_API_KEY

TTS_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"


def _voice_config() -> dict:
    with open(CONFIG_DIR / "voice.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((requests.RequestException,)),
    reraise=True,
)
def synthesize(text: str, out_path: Path) -> Path:
    cfg = _voice_config()
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": cfg["language_code"],
            "name": cfg["voice_name"],
        },
        "audioConfig": {
            "audioEncoding": cfg["audio_encoding"],
            "speakingRate": cfg["speaking_rate"],
            "pitch": cfg["pitch"],
            "sampleRateHertz": cfg["sample_rate_hertz"],
        },
    }
    resp = requests.post(
        TTS_ENDPOINT,
        params={"key": GOOGLE_TTS_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    audio_content = resp.json()["audioContent"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(audio_content))
    return out_path
