# Property Listing Parser (AWS Bedrock)

Extract units, beds, and baths from property listing text (`public_remark`) using Amazon Nova Lite. Drops illogical rows (e.g. baths > beds) and returns clean JSON.

## Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set `AWS_BEARER_TOKEN_BEDROCK` with your Bedrock API key.
3. Enable Nova Lite in the [Bedrock console](https://console.aws.amazon.com/bedrock) (Model access).

## Usage

```bash
# Use built-in example
python property_parser.py

# Use your JSON file
python property_parser.py properties.json
```

**Input JSON shape:** `{"properties": [{"comp_id", "bed", "bath", "public_remark"}, ...]}`  
**Output:** `{"properties": [{"property_id", "units", "beds", "baths"}, ...]}` — illogical entries removed.

## Project Structure

```
├── .env.example
├── config.py          # Region, model, inference settings; loads .env
├── bedrock_client.py   # Nova Lite client (generate_text)
├── property_parser.py  # Main: parse listings → clean JSON
├── requirements.txt
└── README.md
```
