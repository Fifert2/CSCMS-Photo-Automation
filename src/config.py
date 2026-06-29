import json
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


CSCMS_ROOT = Path(os.getenv("CSCMS_ROOT", "")).expanduser()

PHOTOS_TO_REVIEW = CSCMS_ROOT / "Photos to Review"
AI_SELECTED_PHOTOS = CSCMS_ROOT / "AI Selected Photos"
READY_FOR_APPROVAL = CSCMS_ROOT / "Ready for Approval"
BRAND_ASSETS = CSCMS_ROOT / "Brand Assets"
LOGS = CSCMS_ROOT / "Logs"

LOWER_THIRD_PATH = BRAND_ASSETS / "RPI-CSCMS-Automate-Lower-Third.png"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
SELECTION_THRESHOLD = int(os.getenv("SELECTION_THRESHOLD", "7"))

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

PLATFORM_SIZES_PATH = PROJECT_ROOT / "config" / "platform_sizes.json"


def load_platform_sizes() -> dict:
    if not PLATFORM_SIZES_PATH.exists():
        raise FileNotFoundError(f"Missing platform sizes file: {PLATFORM_SIZES_PATH}")

    with open(PLATFORM_SIZES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_directories() -> None:
    required_dirs = [
        PHOTOS_TO_REVIEW,
        AI_SELECTED_PHOTOS,
        READY_FOR_APPROVAL,
        BRAND_ASSETS,
        LOGS,
    ]

    for folder in required_dirs:
        folder.mkdir(parents=True, exist_ok=True)

    for platform_name in load_platform_sizes().keys():
        (READY_FOR_APPROVAL / platform_name).mkdir(parents=True, exist_ok=True)


def validate_setup(require_lower_third: bool = False) -> None:
    if not CSCMS_ROOT.exists():
        raise FileNotFoundError(f"CSCMS_ROOT does not exist: {CSCMS_ROOT}")

    ensure_directories()

    if require_lower_third and not LOWER_THIRD_PATH.exists():
        raise FileNotFoundError(
            f"Missing lower-third PNG: {LOWER_THIRD_PATH}\n"
            "Place the real lower-third file there or create a temporary placeholder."
        )