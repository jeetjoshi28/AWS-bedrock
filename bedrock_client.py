"""Bedrock client for property parser (Amazon Nova Lite)."""

import boto3

from config import REGION, MODEL, MAX_TOKENS, TEMPERATURE, TOP_P


def generate_text(prompt: str, max_tokens: int | None = None) -> str:
    """Send prompt to Nova Lite; return response text."""
    client = boto3.client("bedrock-runtime", region_name=REGION)
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    tokens = max_tokens or MAX_TOKENS

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
