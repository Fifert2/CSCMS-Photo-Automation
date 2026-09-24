from pathlib import Path

from PIL import Image, ImageOps

from config import LOWER_THIRD_PATH, READY_FOR_APPROVAL, load_platform_sizes


def crop_to_aspect(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """
    Center-crops an image to the requested aspect ratio, then resizes it.
    This is deterministic and repeatable.
    """
    image = ImageOps.exif_transpose(image).convert("RGB")

    source_width, source_height = image.size
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        new_width = int(source_height * target_ratio)
        left = (source_width - new_width) // 2
        crop_box = (left, 0, left + new_width, source_height)
    else:
        new_height = int(source_width / target_ratio)
        top = (source_height - new_height) // 2
        crop_box = (0, top, source_width, top + new_height)

    cropped = image.crop(crop_box)
    return cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)


def apply_lower_third(canvas: Image.Image, lower_third: Image.Image) -> Image.Image:
    """
    Adds the lower-third PNG to the output image.
    Vertical formats get more bottom margin to reduce platform UI overlap.
    """
    canvas = canvas.convert("RGBA")
    lower_third = lower_third.convert("RGBA")

    target_width, target_height = canvas.size
    is_vertical = target_height > target_width * 1.4

    if is_vertical:
        overlay_width = int(target_width * 0.94)
        bottom_margin = int(target_height * 0.115)
    else:
        overlay_width = target_width
        bottom_margin = 0

    overlay_height = int(lower_third.height * (overlay_width / lower_third.width))

    max_overlay_height = int(target_height * 0.22)
    if overlay_height > max_overlay_height:
        overlay_height = max_overlay_height
        overlay_width = int(lower_third.width * (overlay_height / lower_third.height))

    overlay = lower_third.resize(
        (overlay_width, overlay_height),
        Image.Resampling.LANCZOS,
    )

    x = (target_width - overlay_width) // 2
    y = target_height - overlay_height - bottom_margin

    if y < 0:
        y = 0

    canvas.alpha_composite(overlay, (x, y))
    return canvas.convert("RGB")


def process_photo(image_path: Path) -> list[Path]:
    """
    Creates platform-specific versions of one selected photo.
    Returns a list of output paths.
    """
    if not LOWER_THIRD_PATH.exists():
        raise FileNotFoundError(f"Missing lower-third PNG: {LOWER_THIRD_PATH}")

    platform_sizes = load_platform_sizes()
    original = Image.open(image_path)
    lower_third = Image.open(LOWER_THIRD_PATH)

    outputs = []

    for platform_name, size_info in platform_sizes.items():
        target_width = int(size_info["width"])
        target_height = int(size_info["height"])

        output_folder = READY_FOR_APPROVAL / platform_name
        output_folder.mkdir(parents=True, exist_ok=True)

        cropped = crop_to_aspect(original, target_width, target_height)
        final_image = apply_lower_third(cropped, lower_third)

        output_path = output_folder / f"{image_path.stem}__{platform_name}.jpg"
        final_image.save(output_path, quality=92, optimize=True)

        outputs.append(output_path)

    return outputs