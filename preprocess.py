from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2


# ============================================================
# Standard processing size
# ============================================================

TARGET_WIDTH = 1024
TARGET_HEIGHT = 1024


# ============================================================
# Resolution normalization
# ============================================================

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

    # Preserve aspect ratio
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


# ============================================================
# Adaptive contrast enhancement
# ============================================================

def enhance_sonar_contrast(image):
    """
    Enhance local contrast in sonar imagery.

    CLAHE is used instead of applying a very strong global
    contrast enhancement. This helps preserve local sonar
    structures while improving visibility in darker regions.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.array(
        image.convert("L"),
        dtype=np.uint8
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    return Image.fromarray(
        enhanced,
        mode="L"
    )


# ============================================================
# Noise reduction
# ============================================================

def reduce_sonar_noise(image):
    """
    Reduce small-scale noise while attempting to preserve
    meaningful sonar structures.

    A small median filter is used first, followed by a mild
    Gaussian filter.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.array(
        image.convert("L"),
        dtype=np.uint8
    )

    # Median filtering is useful for isolated speckle-like noise.
    median = cv2.medianBlur(
        gray,
        3
    )

    # Mild Gaussian smoothing removes very small fluctuations
    # without applying excessive blur.
    filtered = cv2.GaussianBlur(
        median,
        (3, 3),
        0
    )

    return Image.fromarray(
        filtered,
        mode="L"
    )


# ============================================================
# Image quality analysis
# ============================================================

def calculate_preprocessing_quality(image):
    """
    Calculate simple image-quality measurements before/after
    preprocessing.

    Returns:
        dictionary containing brightness, contrast and
        sharpness measurements.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.array(
        image.convert("L"),
        dtype=np.uint8
    )

    brightness = float(np.mean(gray))

    contrast = float(np.std(gray))

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    # Approximate normalized quality components.
    brightness_score = 1.0 - min(
        abs(brightness - 127.5) / 127.5,
        1.0
    )

    contrast_score = min(
        contrast / 64.0,
        1.0
    )

    sharpness_score = min(
        sharpness / 500.0,
        1.0
    )

    quality_score = (
        0.35 * brightness_score
        + 0.40 * contrast_score
        + 0.25 * sharpness_score
    )

    return {
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "quality_score": round(
            quality_score * 100.0,
            2
        )
    }


# ============================================================
# Possible dropout detection
# ============================================================

def detect_possible_dropouts(
    image,
    tile_size=32
):
    """
    Detect unusually uniform dark/bright image blocks.

    This is an image-quality warning only.

    It does NOT prove that sonar data was dropped because
    true dropout diagnosis requires the original sonar
    acquisition data.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.array(
        image.convert("L"),
        dtype=np.uint8
    )

    height, width = gray.shape

    if (
        height < tile_size
        or width < tile_size
    ):
        return {
            "dropout_detected": False,
            "dropout_percentage": 0.0,
            "suspicious_tiles": 0,
            "total_tiles": 0
        }

    suspicious_tiles = 0
    total_tiles = 0

    for y in range(
        0,
        height - tile_size + 1,
        tile_size
    ):
        for x in range(
            0,
            width - tile_size + 1,
            tile_size
        ):

            tile = gray[
                y:y + tile_size,
                x:x + tile_size
            ]

            tile_mean = float(
                np.mean(tile)
            )

            tile_std = float(
                np.std(tile)
            )

            # Extremely uniform black/white regions can indicate
            # missing, saturated or corrupted image regions.
            uniform = tile_std < 3.0

            extremely_dark = (
                tile_mean <= 3.0
            )

            extremely_bright = (
                tile_mean >= 252.0
            )

            if (
                uniform
                and (
                    extremely_dark
                    or extremely_bright
                )
            ):
                suspicious_tiles += 1

            total_tiles += 1

    dropout_percentage = (
        100.0 * suspicious_tiles / total_tiles
        if total_tiles > 0
        else 0.0
    )

    return {
        "dropout_detected": bool(
            dropout_percentage >= 1.0
        ),
        "dropout_percentage": round(
            dropout_percentage,
            2
        ),
        "suspicious_tiles": suspicious_tiles,
        "total_tiles": total_tiles
    }


# ============================================================
# Complete sonar preprocessing pipeline
# ============================================================

def preprocess_sonar_image(image):
    """
    Complete sonar preprocessing pipeline.

    Steps:
        1. Resolution normalization
        2. Grayscale conversion
        3. Adaptive local contrast enhancement
        4. Median + mild Gaussian noise reduction
        5. Conversion back to RGB for YOLO

    Returns:
        PIL RGB image
    """

    if image is None:
        raise ValueError("Input image is None.")

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
    # 3. Adaptive contrast enhancement
    # --------------------------------------------------------

    enhanced = enhance_sonar_contrast(
        gray
    )

    # --------------------------------------------------------
    # 4. Noise reduction
    # --------------------------------------------------------

    filtered = reduce_sonar_noise(
        enhanced
    )

    # --------------------------------------------------------
    # 5. Convert back to RGB for YOLO
    # --------------------------------------------------------

    processed = filtered.convert(
        "RGB"
    )

    return processed


# ============================================================
# Full preprocessing + quality analysis
# ============================================================

def preprocess_with_analysis(image):
    """
    Run preprocessing together with image-quality analysis.

    Returns:
        processed_image
        analysis_dictionary
    """

    if image is None:
        raise ValueError("Input image is None.")

    # Analyze original image first.
    original_quality = calculate_preprocessing_quality(
        image
    )

    dropout_analysis = detect_possible_dropouts(
        image
    )

    # Process the image.
    processed = preprocess_sonar_image(
        image
    )

    # Analyze processed image.
    processed_quality = calculate_preprocessing_quality(
        processed
    )

    warnings = []

    if original_quality["quality_score"] < 40:
        warnings.append(
            "Low original image quality"
        )

    if original_quality["contrast"] < 15:
        warnings.append(
            "Low original image contrast"
        )

    if dropout_analysis["dropout_detected"]:
        warnings.append(
            "Possible data dropout or saturated region detected"
        )

    analysis = {
        "original_quality": original_quality,
        "processed_quality": processed_quality,
        "dropout_analysis": dropout_analysis,
        "warnings": warnings
    }

    return processed, analysis

What changed from your old file?

The important additions are:

- CLAHE adaptive contrast enhancement
- Median + mild Gaussian noise reduction
- image-quality scoring
- possible dropout detection
- "preprocess_with_analysis()" so "app.py" can later use both the processed image and quality information.

And importantly, the actual preprocessing is still returned as a normal RGB PIL image, so it remains compatible with your YOLO pipeline.

For now, only replace "preprocess.py" and commit it. Don't modify "app.py" yet. Then tell me when it's committed, and we'll integrate both "preprocess.py" and the new "sonar_analysis.py" into "app.py" carefully.
