# Property Parser (AWS Bedrock)

A Python tool that uses **Amazon Nova Lite** via AWS Bedrock to correct and enrich residential property data by analyzing listing descriptions. It identifies concrete statements in listing text that clarify or correct unit counts, bedrooms, and bathrooms when the original property records are messy or inconsistent.

---

## What This Project Does

Property data for small residential properties (typically 2–4 units) is often messy and incorrect. This project:

1. **Accepts property data** — Original units, beds, baths, and listing descriptions for each property.
2. **Sends data to Amazon Nova Lite** — Uses AWS Bedrock’s Nova Lite model to read listing descriptions and look for concrete statements about units, beds, and baths.
3. **Returns corrected or clarified values** — When the model finds clear evidence in the listing text, it returns updated counts; otherwise it returns `null` for that field.

### Example Scenarios

| Scenario | Original Data | Listing Description | Result |
|----------|---------------|---------------------|--------|
| Per-unit clarification | 2 units, 2 beds, 1 bath | "Great duplex with 2 beds and 1 bath on each side" | 2 units, 4 beds, 2 baths |
| Unit count correction | Duplex | "This quadruplex has four units" | 4 units |
| Per-unit inference | 3 units (triplex) | "Each unit has 3 beds and 1 bath" | 3 units, 9 beds, 3 baths |
| No clear statement | 2 beds, 1 bath | Generic marketing text | `null` for all fields |

The model only updates fields when it finds **concrete, explicit statements** in the listing. If nothing clear is found, it returns `null` so you can keep the original values.

---

## Project Structure

```
├── config.py          # AWS region, model ID, inference settings; loads .env
├── bedrock_client.py   # Bedrock client — sends prompts to Nova Lite
├── property_parser.py  # Main logic: normalize input → call model → clean output
├── requirements.txt   # Python dependencies
├── .env               # AWS credentials (create manually, not committed)
└── README.md
```

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Create a `.env` file in the project root. You can use either:

- **Standard AWS credentials** — Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION`, or use an `AWS_PROFILE`.
- **Bearer token** — If using Bedrock with a bearer token, set `AWS_BEARER_TOKEN_BEDROCK`.

### 3. Enable Nova Lite in Bedrock

1. Open the [AWS Bedrock Console](https://console.aws.amazon.com/bedrock).
2. Go to **Model access** in the left sidebar.
3. Enable **Amazon Nova Lite** for your account/region.

---

## Usage

### Run with Built-in Example Data

```bash
python property_parser.py
```

This uses a sample set of 10 properties with various bed/bath combinations and listing descriptions.

### Run with Your Own JSON File

```bash
python property_parser.py path/to/your/properties.json
```

---

## Input Format

Provide a JSON object with a `properties` array. Each property can use flexible field names:

| Required | Field | Aliases | Description |
|----------|-------|---------|-------------|
| ✓ | `property_id` | `comp_id`, `id` | Unique identifier |
| ✓ | `listing_description` | `public_remark`, `description` | Listing text to analyze |
| ○ | `units` | `unit_count` | Original unit count |
| ○ | `beds` | `bed` | Original bedroom count |
| ○ | `baths` | `bath` | Original bathroom count |

**Example input:**

```json
{
  "properties": [
    {
      "comp_id": 1,
      "bed": 2,
      "bath": 1,
      "public_remark": "Charming 2-bedroom, 1-bath home with a bright living room."
    },
    {
      "property_id": 2,
      "units": 2,
      "beds": 4,
      "baths": 2,
      "listing_description": "Duplex with 2 beds and 1 bath on each side."
    }
  ]
}
```

---

## Output Format

The tool returns a JSON object with a `properties` array. Each property has:

- `property_id` — Same as input
- `units` — Corrected unit count or `null`
- `beds` — Corrected bedroom count or `null`
- `baths` — Corrected bathroom count or `null`

**Example output:**

```json
{
  "properties": [
    {
      "property_id": 1,
      "units": null,
      "beds": 2,
      "baths": 1
    },
    {
      "property_id": 2,
      "units": 2,
      "beds": 4,
      "baths": 2
    }
  ]
}
```

---

## Configuration

Edit `config.py` to change:

| Variable | Default | Description |
|----------|---------|-------------|
| `REGION` | `us-east-1` | AWS region for Bedrock |
| `MODEL` | `amazon.nova-lite-v1:0` | Bedrock model ID |
| `MAX_TOKENS` | `512` | Max tokens per response |
| `TEMPERATURE` | `0.5` | Sampling temperature |
| `TOP_P` | `0.9` | Top-p sampling |

---

## Requirements

- Python 3.10+
- AWS account with Bedrock access
- Nova Lite model enabled in your region

---

## License

This project is provided as-is for personal or internal use.
