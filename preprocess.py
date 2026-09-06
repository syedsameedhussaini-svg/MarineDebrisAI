from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


# Standard processing size
TARGET_WIDTH = 1024
TARGET_HEIGHT = 1024


def normalize_sonar_resolution(image):
    """
    Normalize sonar imagery to a consistent processing resolution.

    The original aspect ratio is preserved by resizing the image
    to fit inside the target dimensions and padding the remaining
    area.

    Returns:
        normalized_image
        scale
        pad_x
        pad_y
    """

    if image is None:
        raise ValueError("Input image is None.")

    image = image.convert("RGB")

    original_width, original_height = image.size

    if original_width <= 0 or original_height <= 0:
        raise ValueError("Invalid image dimensions.")

    # Calculate scale while preserving aspect ratio
    scale = min(
        TARGET_WIDTH / original_width,
        TARGET_HEIGHT / original_height
    )

    new_width = max(
        1,
        int(round(original_width * scale))
    )

    new_height = max(
        1,
        int(round(original_height * scale))
    )

    resized = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    # Create padded canvas
    canvas = Image.new(
        "RGB",
        (TARGET_WIDTH, TARGET_HEIGHT),
        (0, 0, 0)
    )

    pad_x = (TARGET_WIDTH - new_width) // 2
    pad_y = (TARGET_HEIGHT - new_height) // 2

    canvas.paste(
        resized,
        (pad_x, pad_y)
    )

    return canvas, scale, pad_x, pad_y


def preprocess_sonar_image(image):
    """
    Complete sonar preprocessing pipeline.

    Steps:
        1. Resolution normalization
        2. Grayscale conversion
        3. Contrast enhancement
        4. Noise reduction
        5. Conversion back to RGB
    """

    # --------------------------------------------------------
    # 1. Resolution normalization
    # --------------------------------------------------------

    normalized, _, _, _ = normalize_sonar_resolution(
        image
    )

    # --------------------------------------------------------
    # 2. Grayscale conversion
    # --------------------------------------------------------

    gray = normalized.convert("L")

    # --------------------------------------------------------
    # 3. Contrast enhancement
    # --------------------------------------------------------

    contrast = ImageEnhance.Contrast(
        gray
    ).enhance(1.5)

    # --------------------------------------------------------
    # 4. Noise reduction
    # --------------------------------------------------------

    filtered = contrast.filter(
        ImageFilter.MedianFilter(size=3)
    )

    # --------------------------------------------------------
    # 5. Convert back to RGB for YOLO
    # --------------------------------------------------------

    processed = filtered.convert("RGB")

    return processed