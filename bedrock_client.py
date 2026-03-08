"""Bedrock client for property parser (Amazon Nova Lite)."""

import boto3

from config import REGION, MODEL, MAX_TOKENS, TEMPERATURE, TOP_P


def generate_text(
    prompt: str | None = None,
    max_tokens: int | None = None,
    *,
    system_prompt: str | None = None,
    user_content: str | None = None,
) -> str:
    """Send prompt to Nova Lite; return response text.

    Use system_prompt + user_content for prompt caching: the system prompt
    is cached (must be >= 1K tokens for Nova Lite to cache; otherwise
    inference still works but no cache hit).
    """
    client = boto3.client("bedrock-runtime", region_name=REGION)
    tokens = max_tokens or MAX_TOKENS

    if system_prompt is not None and user_content is not None:
        messages = [{"role": "user", "content": [{"text": user_content}]}]
        system = [
            {"text": system_prompt},
            {"cachePoint": {"type": "default"}},
        ]
        response = client.converse(
            modelId=MODEL,
            messages=messages,
            system=system,
            inferenceConfig={
                "maxTokens": tokens,
                "temperature": TEMPERATURE,
                "topP": TOP_P,
            },
        )
    else:
        messages = [{"role": "user", "content": [{"text": prompt or ""}]}]
        response = client.converse(
            modelId=MODEL,
            messages=messages,
            inferenceConfig={
                "maxTokens": tokens,
                "temperature": TEMPERATURE,
                "topP": TOP_P,
            },
        )

    return response["output"]["message"]["content"][0]["text"]
