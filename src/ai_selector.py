import base64
import json
from io import BytesIO
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageOps

from config import OPENAI_API_KEY, OPENAI_MODEL


PHOTO_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10
        },
        "selected_for_resize": {
            "type": "boolean"
        },
        "best_platforms": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "linkedin_landscape",
                    "instagram_square",
                    "vertical_story_tiktok",
                    "youtube_thumbnail"
                ]
            }
        },
        "reason": {
            "type": "string"
        },
        "possible_issues": {
            "type": "string"
        },
        "caption_idea": {
            "type": "string"
        }
    },
    "required": [
        "score",
        "selected_for_resize",
        "best_platforms",
        "reason",
        "possible_issues",
        "caption_idea"
    ],
    "additionalProperties": False
}


def _image_to_data_url(image_path: Path, max_side: int = 1200) -> str:
    """
    Creates a smaller JPEG copy of the image for AI review.
    The original file is not changed.
    """
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((max_side, max_side))

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def score_photo(image_path: Path) -> dict:
    """
    Uses AI to review the photo and decide whether it should be resized.
    AI only selects and explains. It does not edit the photo.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing from your .env file.")

    client = OpenAI(api_key=OPENAI_API_KEY)
    data_url = _image_to_data_url(image_path)

    prompt = """
You are reviewing conference and event photos for RPI CSCMS marketing.

Decide whether this photo should be selected for social media resizing.

Evaluate:
- sharpness and lighting
- clear subject
- professional appearance
- marketing value for robotics, automation, manufacturing, artificial intelligence, students, RPI, or CSCMS
- useful context such as booths, demos, students, robots, signs, or industry activity
- whether the image would work well on LinkedIn, Instagram, vertical social formats, or YouTube thumbnails

Reject photos that are blurry, too dark, awkwardly framed, repetitive, low-value, or likely to look bad after cropping.

Do not identify people by name.
Do not guess sensitive personal information.
Return JSON only.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "photo_selection",
                "schema": PHOTO_SELECTION_SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)