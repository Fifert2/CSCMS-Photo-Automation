from pathlib import Path
from typing import Literal

from ollama import Client
from pydantic import BaseModel, Field

from config import OLLAMA_HOST, OLLAMA_MODEL


PlatformName = Literal[
    "linkedin_landscape",
    "instagram_square",
    "vertical_story_tiktok",
    "youtube_thumbnail",
]


class PhotoSelection(BaseModel):
    score: int = Field(ge=1, le=10)
    selected_for_resize: bool
    best_platforms: list[PlatformName]
    reason: str
    possible_issues: str
    caption_idea: str


def score_photo(image_path: Path) -> dict:
    """
    Uses the Ollama vision model on your homeserver to review the photo.
    The model selects and explains. It does not edit the photo.
    """

    client = Client(host=OLLAMA_HOST)

    prompt = """
Review this event photo for RPI CSCMS social media.

Score it from 1 to 10.

Select it if it is sharp, well-lit, professional, has a clear subject, and would be useful for robotics, automation, manufacturing, artificial intelligence, student, or conference marketing.

Reject it if it is blurry, dark, awkwardly framed, repetitive, or likely to crop poorly.

Do not identify people by name.

Return only valid JSON with:
score, selected_for_resize, best_platforms, reason, possible_issues, caption_idea.
"""

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [str(image_path.resolve())],
            }
        ],
        format=PhotoSelection.model_json_schema(),
        options={
            "temperature": 0,
            "num_ctx": 8192
        },
    )

    content = response["message"]["content"]
    result = PhotoSelection.model_validate_json(content)

    return result.model_dump()