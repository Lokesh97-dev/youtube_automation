"""OpenAI gpt-image-1 wrapper.

Cross-day mascot consistency has two levers: the verbatim character-bible text
in every prompt, and (optionally) the approved reference portrait passed to the
images.edit endpoint. The reference gives the strongest consistency but can
make the model anchor on the portrait's composition instead of building the
requested scene — so it is switchable via `use_reference_image` in
config/video.yaml. Try both early and keep whichever looks better.
"""
import base64
from pathlib import Path
from typing import Optional

import openai
from openai import OpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from pipeline import character_bible, costs
from pipeline.config import OPENAI_API_KEY

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _is_retryable(exc: BaseException) -> bool:
    """Retry transient faults only.

    Blanket-retrying every Exception meant a content-policy rejection or a bad
    API key was re-sent three times at full cost before failing.
    """
    if isinstance(exc, (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError)):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)
def generate_image(
    prompt: str,
    out_path: Path,
    size: str = "1536x1024",
    quality: str = "medium",
    use_reference: bool = True,
    out_dir: Optional[Path] = None,
) -> Path:
    client = _get_client()
    ref = character_bible.reference_image_path() if use_reference else None

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

    if out_dir is not None:
        costs.record_image(out_dir, quality)

    image_bytes = base64.b64decode(result.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(image_bytes)
    return out_path
