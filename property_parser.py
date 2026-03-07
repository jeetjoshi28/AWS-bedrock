"""
Property listing parser.

- Uses Amazon Nova Lite to extract units/beds/baths from `public_remark`.
- Ambiguity/validity is determined by the LLM from the provided JSON + remarks.
"""

import json
import re
import sys

from bedrock_client import generate_text

TASK = """I am working with property data which is for small residential properties, generally 2-4 units, and this data tends to be messy and incorrect. In addition to the recorded property data, we have listing descriptions for each property. By reading these listing descriptions, we can often identify concrete statements in the listing description which provide better clarity for the correct counts for units, beds and baths.

For example, sometimes the original property data will say the property is a duplex, with 2 beds and 1 bath. However the listing description might have a sentence that says "great duplex with 2 beds and 1 bath on each side." This would indicate that the correct unit count is 2, and the correct count for beds and baths is 4 beds and 2 baths. There are a huge multitude of examples and possibilities that could be found within these listing descriptions. In other examples, we have seen properties marked as a duplex, when the listing description says it's a quadruplex, or says that it's four units. In another important example, sometimes the listing description might not provide clarity on the unit counts, but it might include a statement like "each unit has 3 beds and 1 bath." In this instance, we would elect to trust the original unit count on file, which perhaps is a triplex, and therefore the assessed opinion for the counts for units, beds and baths would be 3 units, 9 beds, 3 baths.

For this task, I will send you an array of properties, and each property will include original units, beds, baths, and a listing description. I would like you to read the listing descriptions, and scan it for concrete statements which provide clear indication for accurate counts for units, beds, and/or baths. If a listing description does not contain any concrete statements that make it clear, then I would like you to leave that answer as NULL. However if we do find concrete statements for clarity on units, beds, or baths, then for this property you will return your updated counts for units, beds, and baths for these properties. I will send to you this array of properties, each with a property_id, units, beds, baths and listing description. You will return a JSON with property_id, units, beds, and baths, and for all properties with no concrete information in the listing description, you can return the property ID, and NULL for the other responses.

Return ONLY a single valid JSON object, no other text. Use this exact shape:
{"properties": [{"property_id": <comp_id>, "units": <number or null>, "beds": <number or null>, "baths": <number or null>}, ...]}

Here is the array:
"""


def extract_json(text: str) -> dict:
    """Get JSON from model response (may be wrapped in markdown)."""
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def is_ambiguous_input_row(row: dict) -> bool:
    """
    Deprecated: keep all rows for the model to resolve via `public_remark`.

    The model prompt/output should decide what is ambiguous; we do not pre-filter
    inputs based on local bed/bath heuristics.
    """
    _ = row
    return False


def is_ambiguous_model_row(row: dict) -> bool:
    """
    Deprecated: do not apply local heuristics to model outputs.

    The model decides ambiguity/validity; we keep model output as-is.
    """
    _ = row
    return False


def clean_model_output(data: dict) -> dict:
    """
    Keep model output unchanged.

    We intentionally avoid "cleanup" rules (e.g., beds/baths comparisons) because
    ambiguity is resolved by the LLM using the full JSON context.
    """
    props = data.get("properties", [])
    if not isinstance(props, list):
        return {"properties": []}
    return {"properties": props}


def split_input_rows(input_json: dict) -> tuple[list[dict], list[dict]]:
    """Return (valid_rows, ambiguous_rows) from the input JSON."""
    rows = input_json.get("properties", [])
    return rows, []


def run_parser(input_json: dict) -> dict:
    """
    Main pipeline.

    - Split out ambiguous input rows (not sent to the model).
    - Send only valid rows to Nova Lite.
    - Clean model output from logically incorrect values.
    - Return both outputs in one JSON object.
    """
    valid_rows, ambiguous_rows = split_input_rows(input_json)
    model_input = {"properties": valid_rows}

    prompt = TASK + json.dumps(model_input, indent=2)
    response = generate_text(prompt, max_tokens=2048)
    model_data = extract_json(response)

    return {
        "properties": clean_model_output(model_data).get("properties", []),
        "ambiguous_properties": ambiguous_rows,
    }


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            input_data = json.load(f)
    else:
        input_data = {
        "properties": [
            {"comp_id":1,"bed":2,"bath":1,"public_remark":"Charming 2-bedroom, 1-bath home with a bright living room and cozy kitchen."},
            {"comp_id":2,"bed":3,"bath":2,"public_remark":"Spacious 3-bedroom, 2-bath home ideal for family living."},
            {"comp_id":3,"bed":1,"bath":4,"public_remark":"The listing indicates 4 bathrooms for a 1-bedroom home, which appears incorrect and should be verified."},
            {"comp_id":4,"bed":4,"bath":3,"public_remark":"Beautiful 4-bedroom, 3-bath home with modern finishes and large backyard."},
            {"comp_id":5,"bed":0,"bath":2,"public_remark":"The listing shows 0 bedrooms while indicating 2 bathrooms which may be a data error."},
            {"comp_id":6,"bed":5,"bath":1,"public_remark":"Spacious 5-bedroom, 1-bath home perfect for family living."},
            {"comp_id":7,"bed":2,"bath":2,"public_remark":"Well maintained 2-bedroom, 2-bath home close to schools and parks."},
            {"comp_id":8,"bed":3,"bath":7,"public_remark":"The property lists 7 bathrooms for a 3-bedroom home which seems inconsistent."},
            {"comp_id":9,"bed":4,"bath":2,"public_remark":"Spacious 4-bedroom, 2-bath home perfect for family living."},
            {"comp_id":10,"bed":2,"bath":9,"public_remark":"Listing currently shows 9 bathrooms for a 2-bedroom home which appears incorrect."}
        ]
        }
    try:
        result = run_parser(input_data)
        props = result.get("properties", [])
        print(json.dumps({"properties": props}, indent=2))
        print("--------------------------------------------------------------------------------")

    except Exception as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Could not parse model response: {e}")


if __name__ == "__main__":
    main()
