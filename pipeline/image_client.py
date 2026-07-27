"""OpenAI gpt-image-1 wrapper. Uses the mascot reference image as an edit
input when available, which is the main lever for cross-day visual
consistency (gpt-image-1 accepts image input; DALL-E 3 does not)."""
import base64
from pathlib import Path

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from pipeline.config import OPENAI_API_KEY
from pipeline import character_bible

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def generate_image(prompt: str, out_path: Path, size: str = "1536x1024", quality: str = "medium") -> Path:
    client = _get_client()
    ref = character_bible.reference_image_path()

    if ref is not None:
        with open(ref, "rb") as ref_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=ref_file,
                prompt=prompt,
                size=size,
                quality=quality,
            )
    else:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
        )

    image_bytes = base64.b64decode(result.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    return out_path
