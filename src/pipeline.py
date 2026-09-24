import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from ai_selector import score_photo
from config import (
    AI_SELECTED_PHOTOS,
    IMAGE_EXTENSIONS,
    LOGS,
    PHOTOS_TO_REVIEW,
    SELECTION_THRESHOLD,
    ensure_directories,
    validate_setup,
)
from image_processor import process_photo


def discover_images(folder: Path, limit: Optional[int] = None) -> list:
    images = [
        path for path in folder.iterdir()
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    images = sorted(images)

    if limit:
        return images[:limit]

    return images


def write_log(rows: list[dict]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOGS / f"selection_log_{timestamp}.csv"
    latest_path = LOGS / "selection_log_latest.csv"

    fieldnames = [
        "file_name",
        "score",
        "selected_for_resize",
        "best_platforms",
        "reason",
        "possible_issues",
        "caption_idea",
        "status",
        "outputs",
    ]

    for path in [log_path, latest_path]:
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return latest_path


def run_pipeline(dry_run: bool, limit: Optional[int] = None, threshold: int = SELECTION_THRESHOLD) -> None:
    ensure_directories()

    if not dry_run:
        validate_setup(require_lower_third=True)
    else:
        validate_setup(require_lower_third=False)

    images = discover_images(PHOTOS_TO_REVIEW, limit=limit)

    if not images:
        print(f"No images found in: {PHOTOS_TO_REVIEW}")
        return

    rows = []

    for image_path in images:
        print(f"Reviewing: {image_path.name}")

        try:
            result = score_photo(image_path)

            score = int(result["score"])
            ai_selected = bool(result["selected_for_resize"])
            selected = ai_selected and score >= threshold

            outputs = []

            if selected and dry_run:
                status = "selected_dry_run"

            elif selected and not dry_run:
                selected_copy = AI_SELECTED_PHOTOS / image_path.name
                shutil.copy2(image_path, selected_copy)

                output_paths = process_photo(image_path)
                outputs = [str(path) for path in output_paths]

                status = "processed"

            else:
                status = "not_selected"

            rows.append(
                {
                    "file_name": image_path.name,
                    "score": score,
                    "selected_for_resize": selected,
                    "best_platforms": ", ".join(result["best_platforms"]),
                    "reason": result["reason"],
                    "possible_issues": result["possible_issues"],
                    "caption_idea": result["caption_idea"],
                    "status": status,
                    "outputs": " | ".join(outputs),
                }
            )

        except Exception as error:
            rows.append(
                {
                    "file_name": image_path.name,
                    "score": "",
                    "selected_for_resize": "",
                    "best_platforms": "",
                    "reason": "",
                    "possible_issues": "",
                    "caption_idea": "",
                    "status": f"error: {error}",
                    "outputs": "",
                }
            )

            print(f"ERROR on {image_path.name}: {error}")

    log_path = write_log(rows)
    print(f"Done. Log saved to: {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CSCMS photo automation prototype")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Score photos and create a log only. No files are copied or processed.",
    )

    parser.add_argument(
        "--process",
        action="store_true",
        help="Score photos, copy selected images, process them, and save outputs.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of photos processed during testing.",
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=SELECTION_THRESHOLD,
        help="Minimum AI score required for photo selection.",
    )

    args = parser.parse_args()

    dry_run = True

    if args.process:
        dry_run = False

    if args.dry_run:
        dry_run = True

    run_pipeline(
        dry_run=dry_run,
        limit=args.limit,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()