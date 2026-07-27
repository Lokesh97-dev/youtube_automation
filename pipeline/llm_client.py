"""Anthropic Claude wrapper: retry/backoff + forced-JSON output for the
topic and script generation stages."""
import json

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from pipeline.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


class LLMJSONError(Exception):
    pass


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMJSONError(f"No JSON object found in response: {text[:200]!r}")
    return json.loads(text[start : end + 1])


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((anthropic.APIStatusError, anthropic.APIConnectionError, LLMJSONError)),
    reraise=True,
)
def generate_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
    """Calls Claude and parses the response as a single JSON object. Retries
    on transient API errors and on JSON-parse failures (the model
    occasionally wraps JSON in prose despite instructions)."""
    client = _get_client()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system_prompt + "\n\nRespond with ONLY a single valid JSON object. No prose, no markdown code fences.",
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)
