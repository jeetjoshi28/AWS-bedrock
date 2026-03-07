"""
Property listing parser.

- Uses Amazon Nova Lite to extract units/beds/baths from `public_remark`.
- Removes logically incorrect rows from the final output.
- Also returns a separate list of ambiguous input rows (bad bed/bath data).
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
    True if the *input* row has logically incorrect values.

    Examples:
    - bed <= 0
    - bath <= 0
    - bath > bed
    """
    bed = row.get("bed")
    bath = row.get("bath")

    if not isinstance(bed, int) or not isinstance(bath, int):
        return True
    if bed <= 0 or bath <= 0:
        return True
    return bath > bed


def is_ambiguous_model_row(row: dict) -> bool:
    """
    True if the *model output* row is logically incorrect.

    We only validate when both beds and baths are present.
    """
    beds = row.get("beds")
    baths = row.get("baths")

    if beds is None or baths is None:
        return False
    if not isinstance(beds, int) or not isinstance(baths, int):
        return True
    if beds <= 0 or baths <= 0:
        return True
    return baths > beds


def clean_model_output(data: dict) -> dict:
    """Remove properties with logically incorrect output values."""
    props = data.get("properties", [])
    cleaned = [p for p in props if not is_ambiguous_model_row(p)]
    return {"properties": cleaned}


def split_input_rows(input_json: dict) -> tuple[list[dict], list[dict]]:
    """Return (valid_rows, ambiguous_rows) from the input JSON."""
    rows = input_json.get("properties", [])
    valid = []
    ambiguous = []

    for row in rows:
        if is_ambiguous_input_row(row):
            ambiguous.append(
                {
                    "comp_id": row.get("comp_id"),
                    "bed": row.get("bed"),
                    "bath": row.get("bath"),
                    "public_remark": row.get("public_remark"),
                }
            )
        else:
            valid.append(row)

    return valid, ambiguous


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
  "properties":[
    {"comp_id":1,"bed":2,"bath":1,"public_remark":"Cozy 2 bedroom home with 1 bathroom and spacious living area."},
    {"comp_id":2,"bed":3,"bath":2,"public_remark":"Comfortable 3 bedroom home with 2 bathrooms."},
    {"comp_id":3,"bed":4,"bath":2,"public_remark":"Spacious family home with 4 bedrooms and 2 bathrooms."},
    {"comp_id":4,"bed":5,"bath":3,"public_remark":"Large home offering 5 bedrooms and 3 bathrooms."},
    {"comp_id":5,"bed":3,"bath":1,"public_remark":"Charming 3 bedroom home with 1 bathroom."},
    {"comp_id":6,"bed":4,"bath":3,"public_remark":"Modern 4 bedroom home with 3 bathrooms."},
    {"comp_id":7,"bed":2,"bath":2,"public_remark":"Comfortable 2 bedroom 2 bath property."},
    {"comp_id":8,"bed":3,"bath":2,"public_remark":"Beautiful 3 bedroom, 2 bathroom home."},
    {"comp_id":9,"bed":5,"bath":4,"public_remark":"Spacious 5 bedroom home with 4 bathrooms."},
    {"comp_id":10,"bed":4,"bath":2,"public_remark":"Family friendly 4 bedroom home with 2 bathrooms."},
    {"comp_id":11,"bed":3,"bath":2,"public_remark":"Lovely home offering 3 bedrooms and 2 baths."},
    {"comp_id":12,"bed":2,"bath":1,"public_remark":"Cozy home with 2 bedrooms and 1 bath."},
    {"comp_id":13,"bed":4,"bath":3,"public_remark":"Large family home with 4 bedrooms and 3 baths."},
    {"comp_id":14,"bed":3,"bath":1,"public_remark":"Comfortable 3 bedroom home with single bathroom."},
    {"comp_id":15,"bed":5,"bath":3,"public_remark":"Spacious layout with 5 bedrooms and 3 baths."},
    {"comp_id":16,"bed":4,"bath":2,"public_remark":"Well maintained 4 bedroom home with 2 baths."},
    {"comp_id":17,"bed":2,"bath":2,"public_remark":"Nice 2 bedroom property with 2 bathrooms."},
    {"comp_id":18,"bed":3,"bath":2,"public_remark":"Beautiful 3 bedroom, 2 bath home."},
    {"comp_id":19,"bed":4,"bath":3,"public_remark":"Spacious 4 bedroom 3 bath home."},
    {"comp_id":20,"bed":2,"bath":1,"public_remark":"Comfortable 2 bedroom, 1 bath property."}
  ]
}

    try:
        result = run_parser(input_data)
        valid_count = len(result["properties"])
        error_count = len(result["ambiguous_properties"])
        print(json.dumps({"properties": result["properties"]}, indent=2))
        print("--------------------------------------------------------------------------------")
        print(json.dumps({"ambiguous_properties": result["ambiguous_properties"]}, indent=2))
        print("--------------------------------------------------------------------------------")
        print(f"{valid_count} after cleanup , {error_count} error property")
    except Exception as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Could not parse model response: {e}")


if __name__ == "__main__":
    main()
