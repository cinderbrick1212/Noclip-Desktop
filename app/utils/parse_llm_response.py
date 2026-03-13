"""Shared utility for parsing JSON from LLM text responses."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_json_from_llm_text(text: str) -> dict[str, Any]:
    """Extract and parse the first JSON object from an LLM response string.

    LLMs often wrap their JSON in markdown code fences or add preamble text.
    This function finds the outermost ``{…}`` pair and parses it.

    Returns an empty dict if no valid JSON is found.
    """
    if not text or not text.strip():
        return {}

    stripped = text.strip()
    start_index = stripped.find('{')
    end_index = stripped.rfind('}')

    if start_index == -1 or end_index == -1 or end_index <= start_index:
        logger.warning('No JSON object found in LLM response: %s', stripped[:200])
        return {}

    try:
        return json.loads(stripped[start_index:end_index + 1])
    except json.JSONDecodeError as e:
        logger.warning('Failed to parse JSON from LLM response: %s', e)
        logger.debug('Raw text: %s', stripped[:500])
        return {}
