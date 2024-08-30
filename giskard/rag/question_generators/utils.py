from typing import Optional, Sequence

import json
import logging
import re

from ...llm.client import ChatMessage, LLMClient

try:
    from tqdm.auto import tqdm, trange

    maybe_trange = trange
    maybe_tqdm = tqdm
except ImportError:

    def maybe_trange(*args, **kwargs):
        return range(*args, **kwargs)

    def maybe_tqdm(x, *args, **kwargs):
        return x


logger = logging.getLogger(__name__)


def parse_json_output(
    raw_json: str, llm_client: LLMClient, keys: Optional[Sequence[str]] = None, caller_id: Optional[str] = None
) -> dict:
    try:
        return json.loads(raw_json, strict=False)
    except json.JSONDecodeError:
        logger.debug("JSON decoding error, trying to fix the JSON string.")

    logger.debug("Raw output: %s", raw_json)
    # Let's see if it's just a matter of markdown format (```json ... ```)
    match = re.search(r"```json\s{0,5}(.*?)\s{0,5}```", raw_json, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1), strict=False)
        except json.JSONDecodeError:
            logger.debug("String matching didn't fix the format, trying to fix it with the LLM itself.")
            pass

    # Final attempt, let's try to fix the JSON with the LLM itself
    out = llm_client.complete(
        messages=[
            ChatMessage(
                role="system",
                content="Fix the following text so it contains a single valid JSON object. Make sure to start and end with curly brackets.",
            ),
            ChatMessage(role="user", content=raw_json),
        ],
        temperature=0,
        caller_id=caller_id,
        format="json",
    )

    parsed_dict = json.loads(out.content, strict=False)

    if keys is not None and any([k not in parsed_dict for k in keys]):
        raise ValueError(f"Keys {keys} not found in the JSON output: {parsed_dict}")

    return parsed_dict
