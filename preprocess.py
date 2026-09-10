from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


# ============================================================
# MarineDebrisAI - Sonar Preprocessing
# ============================================================

TARGET_WIDTH = 640
TARGET_HEIGHT = 640


# ============================================================
# Resolution Normalization
# ============================================================

def normalize_sonar_resolution(image):
    """
    Normalize sonar imagery to a consistent processing resolution.

    The original aspect ratio is preserved. Empty areas are padded
    with black pixels.

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

    canvas = Image.new(
        "RGB",
        (TARGET_WIDTH, TARGET_HEIGHT),
        (0, 0, 0)
    )

    pad_x = (
        TARGET_WIDTH - new_width
    ) // 2

    pad_y = (
        TARGET_HEIGHT - new_height
    ) // 2

    canvas.paste(
        resized,
        (pad_x, pad_y)
    )

    return (
        canvas,
        scale,
        pad_x,
        pad_y
    )


# ============================================================
# Contrast Enhancement
# ============================================================

def enhance_sonar_contrast(image):
    """
    Improve sonar image contrast using Pillow's contrast
    enhancement.

    This is intentionally conservative so that useful acoustic
    structures are not excessively amplified.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = image.convert("L")

    enhanced = ImageEnhance.Contrast(
        gray
    ).enhance(1.5)

    return enhanced


# ============================================================
# Noise Reduction
# ============================================================

def reduce_sonar_noise(image):
    """
    Reduce small-scale image noise using a small median filter.

    Median filtering is useful for reducing isolated noise while
    preserving many object boundaries.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = image.convert("L")

    filtered = gray.filter(
        ImageFilter.MedianFilter(
            size=3
        )
    )

    return filtered


# ============================================================
# Image Quality Analysis
# ============================================================

def calculate_preprocessing_quality(image):
    """
    Calculate basic image-quality measurements.

    Measurements:
        brightness
        contrast
        sharpness estimate
        overall quality score

    The score is an image-quality indicator only. It is NOT an
    AI detection confidence score.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.asarray(
        image.convert("L"),
        dtype=np.float32
    )

    if gray.size == 0:
        raise ValueError("Image contains no pixels.")

    brightness = float(
        np.mean(gray)
    )

    contrast = float(
        np.std(gray)
    )

    # Simple sharpness approximation using neighboring
    # pixel differences. This avoids OpenCV.
    horizontal_difference = np.abs(
        np.diff(gray, axis=1)
    )

    vertical_difference = np.abs(
        np.diff(gray, axis=0)
    )

    horizontal_score = (
        float(np.mean(horizontal_difference))
        if horizontal_difference.size > 0
        else 0.0
    )

    vertical_score = (
        float(np.mean(vertical_difference))
        if vertical_difference.size > 0
        else 0.0
    )

    sharpness = (
        horizontal_score
        + vertical_score
    ) / 2.0

    # --------------------------------------------------------
    # Normalize quality components
    # --------------------------------------------------------

    brightness_score = 1.0 - min(
        abs(brightness - 127.5) / 127.5,
        1.0
    )

    contrast_score = min(
        contrast / 64.0,
        1.0
    )

    sharpness_score = min(
        sharpness / 32.0,
        1.0
    )

    quality_score = (
        0.35 * brightness_score
        + 0.40 * contrast_score
        + 0.25 * sharpness_score
    )

    return {
        "brightness": round(
            brightness,
            2
        ),

        "contrast": round(
            contrast,
            2
        ),

        "sharpness": round(
            sharpness,
            2
        ),

        "quality_score": round(
            quality_score * 100.0,
            2
        )
    }


# ============================================================
# Possible Dropout Detection
# ============================================================

def detect_possible_dropouts(
    image,
    tile_size=32
):
    """
    Detect unusually uniform dark or bright regions.

    This is only an image-quality warning.

    It cannot prove actual sonar data dropout because true
    dropout diagnosis requires the original sonar acquisition
    and navigation data.
    """

    if image is None:
        raise ValueError("Input image is None.")

    gray = np.asarray(
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

            uniform = (
                tile_std < 3.0
            )

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
        100.0
        * suspicious_tiles
        / total_tiles
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

        "suspicious_tiles":
            suspicious_tiles,

        "total_tiles":
            total_tiles
    }


# ============================================================
# Complete Sonar Preprocessing
# ============================================================

def preprocess_sonar_image(image):
    """
    Complete sonar preprocessing pipeline.

    Steps:
        1. Resolution normalization
        2. Grayscale conversion
        3. Contrast enhancement
        4. Median noise reduction
        5. RGB conversion for YOLO

    Returns:
        PIL RGB image
    """

    if image is None:
        raise ValueError("Input image is None.")

    # --------------------------------------------------------
    # 1. Resolution normalization
    # --------------------------------------------------------

    normalized, _, _, _ = (
        normalize_sonar_resolution(
            image
        )
    )

    # --------------------------------------------------------
    # 2. Grayscale conversion
    # --------------------------------------------------------

    gray = normalized.convert(
        "L"
    )

    # --------------------------------------------------------
    # 3. Contrast enhancement
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
    # 5. Convert back to RGB
    # --------------------------------------------------------

    processed = filtered.convert(
        "RGB"
    )

    return processed


# ============================================================
# Preprocessing + Analysis
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

    # --------------------------------------------------------
    # Analyze original image
    # --------------------------------------------------------

    original_quality = (
        calculate_preprocessing_quality(
            image
        )
    )

    dropout_analysis = (
        detect_possible_dropouts(
            image
        )
    )

    # --------------------------------------------------------
    # Process image
    # --------------------------------------------------------

    processed = preprocess_sonar_image(
        image
    )

    # --------------------------------------------------------
    # Analyze processed image
    # --------------------------------------------------------

    processed_quality = (
        calculate_preprocessing_quality(
            processed
        )
    )

    # --------------------------------------------------------
    # Generate warnings
    # --------------------------------------------------------

    warnings = []

    if (
        original_quality["quality_score"]
        < 40
    ):

        warnings.append(
            "Low original image quality"
        )

    if (
        original_quality["contrast"]
        < 15
    ):

        warnings.append(
            "Low original image contrast"
        )

    if (
        dropout_analysis[
            "dropout_detected"
        ]
    ):

        warnings.append(
            "Possible data dropout or saturated "
            "region detected"
        )

    # --------------------------------------------------------
    # Final analysis object
    # --------------------------------------------------------

    analysis = {

        "original_quality":
            original_quality,

        "processed_quality":
            processed_quality,

        "dropout_analysis":
            dropout_analysis,

        "warnings":
            warnings
    }

    return (
        processed,
        analysis
    )
