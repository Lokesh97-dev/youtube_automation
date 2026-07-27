"""Anthropic Claude wrapper: retry/backoff + forced-JSON output for the
topic and script generation stages."""
import json
from pathlib import Path
from typing import Optional

import anthropic
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from pipeline import costs
from pipeline.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


class LLMJSONError(Exception):
    """The model returned something that isn't a usable JSON object."""


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMJSONError(f"No JSON object found in response: {text[:200]!r}")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        # Wrapped so the retry policy treats malformed JSON the same as
        # missing JSON — both are usually fixed by simply asking again.
        raise LLMJSONError(f"Malformed JSON in response: {exc}") from exc


def _is_retryable(exc: BaseException) -> bool:
    """Retry transient faults only. A 400/401/403 will never succeed on
    retry, and retrying it just burns budget and delays the failure."""
    if isinstance(exc, (LLMJSONError, anthropic.APIConnectionError, anthropic.RateLimitError)):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)
def generate_json(
    system_prompt: str, user_prompt: str, max_tokens: int = 2000, out_dir: Optional[Path] = None
) -> dict:
    """Call Claude and parse the response as a single JSON object.

    Both the API call and the JSON parse sit inside the retry boundary, so a
    response that arrives as prose or truncated JSON is re-requested rather
    than failing the whole run. Token usage is recorded per attempt, since
    every attempt is billed.
    """
    client = _get_client()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system_prompt
        + "\n\nRespond with ONLY a single valid JSON object. No prose, no markdown code fences.",
        messages=[{"role": "user", "content": user_prompt}],
    )
    if out_dir is not None:
        costs.record_llm(out_dir, response.usage.input_tokens, response.usage.output_tokens)

    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)
