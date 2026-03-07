"""AWS Bedrock configuration."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env so AWS_BEARER_TOKEN_BEDROCK is set before any boto3 call
load_dotenv(Path(__file__).resolve().parent / ".env")

# AWS region (change if needed)
REGION = "us-east-1"

# Amazon Nova Lite (prompt only)
MODEL = "amazon.nova-lite-v1:0"

# Inference settings
MAX_TOKENS = 512
TEMPERATURE = 0.5
TOP_P = 0.9
