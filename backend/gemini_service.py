import json
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image
from pydantic import ValidationError

from .models import FloorPlan

PROMPT = """Analyze this floor-plan image. Return a JSON object only, with no Markdown fences.
Identify all visible structural walls and windows. Coordinates must be normalized from 0 to 1
relative to the full uploaded image (not a cropped plan). Use wall IDs that windows reference.
Do not invent doors, furniture, labels, or measurements. If no geometry is reliable, return
empty walls and windows arrays.

Use exactly this JSON shape (the server adds image dimensions):
{
  "walls": [{"id": "wall-1", "start": {"x": 0.1, "y": 0.2}, "end": {"x": 0.8, "y": 0.2}, "thickness": 0.01, "confidence": 0.9}],
  "windows": [{"id": "window-1", "start": {"x": 0.3, "y": 0.2}, "end": {"x": 0.4, "y": 0.2}, "wallId": "wall-1", "confidence": 0.9}]
}"""


class GeminiParseError(Exception):
    """Safe public-facing parsing failure."""


def image_dimensions(content: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(content)) as image:
        return image.width, image.height


def _response_payload(response: object) -> dict:
    """Accommodate both structured and text JSON returned by google-genai."""
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        if hasattr(parsed, "model_dump"):
            parsed = parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed

    text = getattr(response, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise GeminiParseError("The analysis service returned no geometry.")
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise GeminiParseError("The analysis service returned invalid geometry.")
    return parsed


def validate_gemini_payload(payload: dict, width: int, height: int) -> FloorPlan:
    """Add server-owned metadata before strictly validating Gemini geometry."""
    geometry = {
        "image": {"width": width, "height": height},
        "walls": payload.get("walls", []),
        "windows": payload.get("windows", []),
    }
    if not isinstance(geometry["walls"], list) or not isinstance(
        geometry["windows"], list
    ):
        raise ValueError("walls and windows must be arrays")
    return FloorPlan.model_validate(geometry)


def parse_floor_plan(
    content: bytes, mime_type: str, api_key: str, model: str
) -> FloorPlan:
    try:
        width, height = image_dimensions(content)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=[PROMPT, types.Part.from_bytes(data=content, mime_type=mime_type)],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )
        return validate_gemini_payload(_response_payload(response), width, height)
    except (ValidationError, json.JSONDecodeError, OSError, ValueError) as exc:
        raise GeminiParseError(
            "The analysis service returned an invalid floor-plan response."
        ) from exc
    except GeminiParseError:
        raise
    except Exception as exc:
        raise GeminiParseError(
            "The floor-plan analysis service is temporarily unavailable."
        ) from exc
