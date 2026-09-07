"""
MarineDebrisAI - Optimized Sonar Image Analysis Module

Provides image-based analysis for side-scan sonar imagery:
- Image quality assessment
- Possible data-dropout detection
- Local contrast/texture analysis
- Edge/structure analysis
- Shadow-like region analysis
- Detection validation support

Important:
This module does NOT perform true INS/GPS-based heave, pitch, or roll
correction. That requires the original sonar/navigation metadata.

Designed for efficient execution on Streamlit Cloud / CPU systems.
"""

from __future__ import annotations

from typing import Dict, Tuple

import cv2
import numpy as np


# ============================================================
# Utility functions
# ============================================================

def _safe_float(value, default=0.0):
    """Convert a value to a finite float."""
    try:
        value = float(value)

        if np.isfinite(value):
            return value

        return default

    except (TypeError, ValueError):
        return default


def _clip01(value):
    """Clamp a value to 0-1."""
    return float(
        np.clip(value, 0.0, 1.0)
    )


def _to_gray(image):
    """Safely convert an image to grayscale."""

    if image is None:
        raise ValueError("Image is None.")

    if not isinstance(image, np.ndarray):
        image = np.asarray(image)

    if image.size == 0:
        raise ValueError("Image is empty.")

    if len(image.shape) == 2:
        gray = image

    elif image.shape[2] == 4:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGRA2GRAY
        )

    else:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

    return gray.astype(np.uint8)


# ============================================================
# Image quality
# ============================================================

def calculate_image_quality(image):
    """
    Calculate basic image-quality measurements.

    Returns:
        brightness
        contrast
        sharpness
        quality_score
    """

    gray = _to_gray(image)

    brightness = float(
        np.mean(gray)
    )

    contrast = float(
        np.std(gray)
    )

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    brightness_score = (
        1.0
        - min(
            abs(brightness - 127.5) / 127.5,
            1.0
        )
    )

    contrast_score = _clip01(
        contrast / 64.0
    )

    sharpness_score = _clip01(
        sharpness / 500.0
    )

    quality_score = (
        0.35 * brightness_score
        + 0.40 * contrast_score
        + 0.25 * sharpness_score
    )

    return {
        "brightness": round(
            brightness,
            3
        ),

        "contrast": round(
            contrast,
            3
        ),

        "sharpness": round(
            sharpness,
            3
        ),

        "quality_score": round(
            quality_score * 100.0,
            2
        ),
    }


# ============================================================
# Dropout detection
# ============================================================

def detect_data_dropouts(
    image,
    tile_size=32
):
    """
    Detect suspicious uniform dark/bright regions.

    This is an image-quality indicator only.
    It is NOT definitive sonar data-loss detection.
    """

    gray = _to_gray(image)

    height, width = gray.shape

    if (
        height < tile_size
        or width < tile_size
    ):
        return {
            "dropout_detected": False,
            "dropout_percentage": 0.0,
            "dropout_tiles": 0,
            "total_tiles": 0,
        }

    # Crop image to complete tiles.
    usable_height = (
        height // tile_size
    ) * tile_size

    usable_width = (
        width // tile_size
    ) * tile_size

    cropped = gray[
        :usable_height,
        :usable_width
    ]

    # Reshape into tiles.
    tiles = cropped.reshape(
        usable_height // tile_size,
        tile_size,
        usable_width // tile_size,
        tile_size
    )

    # Move tile dimensions together.
    tiles = tiles.transpose(
        0,
        2,
        1,
        3
    )

    tile_means = np.mean(
        tiles,
        axis=(2, 3)
    )

    tile_stds = np.std(
        tiles,
        axis=(2, 3)
    )

    uniform = tile_stds < 3.0

    extremely_dark = (
        tile_means < 3.0
    )

    extremely_bright = (
        tile_means > 252.0
    )

    suspicious = (
        uniform
        & (
            extremely_dark
            | extremely_bright
        )
    )

    suspicious_tiles = int(
        np.count_nonzero(
            suspicious
        )
    )

    total_tiles = int(
        suspicious.size
    )

    percentage = (
        100.0
        * suspicious_tiles
        / total_tiles
        if total_tiles > 0
        else 0.0
    )

    return {
        "dropout_detected": bool(
            percentage >= 1.0
        ),

        "dropout_percentage": round(
            percentage,
            2
        ),

        "dropout_tiles":
            suspicious_tiles,

        "total_tiles":
            total_tiles,
    }


# ============================================================
# Texture analysis
# ============================================================

def calculate_texture_score(image):
    """
    Estimate local intensity variation.

    Higher values indicate stronger local texture.
    This is NOT a debris classification score.
    """

    gray = _to_gray(image)

    gray_float = gray.astype(
        np.float32
    )

    mean = cv2.GaussianBlur(
        gray_float,
        (0, 0),
        3
    )

    squared_mean = cv2.GaussianBlur(
        gray_float * gray_float,
        (0, 0),
        3
    )

    variance = np.maximum(
        squared_mean - mean * mean,
        0
    )

    local_std = np.sqrt(
        variance
    )

    score = float(
        np.mean(local_std)
    )

    return round(
        _clip01(
            score / 32.0
        ) * 100.0,
        2
    )


# ============================================================
# Edge analysis
# ============================================================

def calculate_edge_score(image):
    """
    Calculate the proportion of strong edges.
    """

    gray = _to_gray(image)

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    edge_percentage = (
        100.0
        * float(
            np.count_nonzero(edges)
        )
        / edges.size
    )

    score = _clip01(
        edge_percentage / 20.0
    ) * 100.0

    return round(
        score,
        2
    )


# ============================================================
# Shadow-like analysis
# ============================================================

def analyze_shadow_like_region(
    image,
    bbox
):
    """
    Look for a darker region immediately after a detected object.

    This is only shadow-like image evidence.
    It does NOT prove a physically correct acoustic shadow.
    """

    gray = _to_gray(image)

    height, width = gray.shape

    x1, y1, x2, y2 = [
        int(v)
        for v in bbox
    ]

    x1 = max(
        0,
        min(x1, width - 1)
    )

    x2 = max(
        0,
        min(x2, width)
    )

    y1 = max(
        0,
        min(y1, height - 1)
    )

    y2 = max(
        0,
        min(y2, height)
    )

    if (
        x2 <= x1
        or y2 <= y1
    ):
        return {
            "shadow_score": 0.0,
            "object_mean": 0.0,
            "background_mean": 0.0,
            "shadow_mean": 0.0,
        }

    object_region = gray[
        y1:y2,
        x1:x2
    ]

    if object_region.size == 0:
        return {
            "shadow_score": 0.0,
            "object_mean": 0.0,
            "background_mean": 0.0,
            "shadow_mean": 0.0,
        }

    object_mean = float(
        np.mean(object_region)
    )

    # --------------------------------------------------------
    # Background region
    # --------------------------------------------------------

    margin_x = max(
        5,
        int((x2 - x1) * 0.5)
    )

    margin_y = max(
        5,
        int((y2 - y1) * 0.5)
    )

    bx1 = max(
        0,
        x1 - margin_x
    )

    bx2 = min(
        width,
        x2 + margin_x
    )

    by1 = max(
        0,
        y1 - margin_y
    )

    by2 = min(
        height,
        y2 + margin_y
    )

    background_region = gray[
        by1:by2,
        bx1:bx2
    ]

    if background_region.size > 0:

        background_mean = float(
            np.mean(
                background_region
            )
        )

    else:

        background_mean = object_mean

    # --------------------------------------------------------
    # Shadow region
    # --------------------------------------------------------

    shadow_width = max(
        5,
        int((x2 - x1) * 1.5)
    )

    sx1 = x2

    sx2 = min(
        width,
        x2 + shadow_width
    )

    shadow_region = gray[
        y1:y2,
        sx1:sx2
    ]

    if shadow_region.size > 0:

        shadow_mean = float(
            np.mean(
                shadow_region
            )
        )

    else:

        shadow_mean = background_mean

    darkness_difference = max(
        0.0,
        background_mean - shadow_mean
    )

    shadow_score = (
        _clip01(
            darkness_difference / 60.0
        )
        * 100.0
    )

    return {
        "shadow_score": round(
            shadow_score,
            2
        ),

        "object_mean": round(
            object_mean,
            2
        ),

        "background_mean": round(
            background_mean,
            2
        ),

        "shadow_mean": round(
            shadow_mean,
            2
        ),
    }


# ============================================================
# Detection validation
# ============================================================

def validate_detection(
    image,
    bbox,
    model_confidence
):
    """
    Validate a YOLO detection using lightweight
    image-based supporting evidence.

    Important optimization:
    Full-image metrics are calculated ONCE here using
    cached results whenever possible.

    The function remains compatible with the existing app.py.
    """

    # --------------------------------------------------------
    # Convert image
    # --------------------------------------------------------

    gray = _to_gray(image)

    # --------------------------------------------------------
    # Image quality
    # --------------------------------------------------------

    brightness = float(
        np.mean(gray)
    )

    contrast = float(
        np.std(gray)
    )

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    brightness_score = (
        1.0
        - min(
            abs(brightness - 127.5)
            / 127.5,
            1.0
        )
    )

    contrast_score = _clip01(
        contrast / 64.0
    )

    sharpness_score = _clip01(
        sharpness / 500.0
    )

    quality_score = (
        0.35 * brightness_score
        + 0.40 * contrast_score
        + 0.25 * sharpness_score
    ) * 100.0

    quality_score = round(
        quality_score,
        2
    )

    # --------------------------------------------------------
    # Shadow analysis
    #
    # This is the only strongly detection-specific analysis.
    # --------------------------------------------------------

    shadow = analyze_shadow_like_region(
        gray,
        bbox
    )

    # --------------------------------------------------------
    # Lightweight local texture around detection
    #
    # Instead of processing the entire image again, use
    # the detected region.
    # --------------------------------------------------------

    height, width = gray.shape

    x1, y1, x2, y2 = [
        int(v)
        for v in bbox
    ]

    x1 = max(
        0,
        min(x1, width - 1)
    )

    x2 = max(
        0,
        min(x2, width)
    )

    y1 = max(
        0,
        min(y1, height - 1)
    )

    y2 = max(
        0,
        min(y2, height)
    )

    if (
        x2 > x1
        and y2 > y1
    ):

        roi = gray[
            y1:y2,
            x1:x2
        ]

        if roi.size > 0:

            texture_value = float(
                np.std(roi)
            )

        else:

            texture_value = 0.0

    else:

        texture_value = 0.0

    texture_score = round(
        _clip01(
            texture_value / 64.0
        ) * 100.0,
        2
    )

    # --------------------------------------------------------
    # Local edge analysis
    # --------------------------------------------------------

    if (
        x2 > x1
        and y2 > y1
    ):

        roi = gray[
            y1:y2,
            x1:x2
        ]

        if roi.size > 0:

            edges = cv2.Canny(
                roi,
                50,
                150
            )

            edge_percentage = (
                100.0
                * float(
                    np.count_nonzero(
                        edges
                    )
                )
                / edges.size
            )

        else:

            edge_percentage = 0.0

    else:

        edge_percentage = 0.0

    edge_score = round(
        _clip01(
            edge_percentage / 20.0
        ) * 100.0,
        2
    )

    # --------------------------------------------------------
    # Dropout check
    #
    # Only perform the inexpensive local check around the
    # detection instead of scanning the complete image.
    # --------------------------------------------------------

    local_dropout = False

    if (
        x2 > x1
        and y2 > y1
    ):

        roi = gray[
            y1:y2,
            x1:x2
        ]

        if roi.size > 0:

            roi_mean = float(
                np.mean(roi)
            )

            roi_std = float(
                np.std(roi)
            )

            local_dropout = (
                roi_std < 3.0
                and (
                    roi_mean < 3.0
                    or roi_mean > 252.0
                )
            )

    # --------------------------------------------------------
    # Model confidence
    # --------------------------------------------------------

    model_confidence = _clip01(
        _safe_float(
            model_confidence
        )
    )

    shadow_normalized = (
        shadow["shadow_score"]
        / 100.0
    )

    quality_normalized = (
        quality_score
        / 100.0
    )

    texture_normalized = (
        texture_score
        / 100.0
    )

    edge_normalized = (
        edge_score
        / 100.0
    )

    # --------------------------------------------------------
    # Final anomaly score
    # --------------------------------------------------------
    #
    # YOLO confidence remains dominant.
    #

    anomaly_score = (
        0.70 * model_confidence
        + 0.12 * shadow_normalized
        + 0.08 * quality_normalized
        + 0.05 * texture_normalized
        + 0.05 * edge_normalized
    )

    anomaly_score = (
        _clip01(
            anomaly_score
        )
        * 100.0
    )

    anomaly_score = round(
        anomaly_score,
        2
    )

    # --------------------------------------------------------
    # Assessment
    # --------------------------------------------------------

    if anomaly_score >= 80:

        assessment = "High"

    elif anomaly_score >= 60:

        assessment = "Moderate"

    else:

        assessment = "Low"

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    warnings = []

    if quality_score < 40:

        warnings.append(
            "Low overall image quality"
        )

    if local_dropout:

        warnings.append(
            "Possible dropout or saturated region near detection"
        )

    if shadow["shadow_score"] < 15:

        warnings.append(
            "Weak shadow-like evidence"
        )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "model_confidence":
            round(
                model_confidence * 100.0,
                2
            ),

        "anomaly_score":
            anomaly_score,

        "assessment":
            assessment,

        "shadow_score":
            shadow["shadow_score"],

        "texture_score":
            texture_score,

        "edge_score":
            edge_score,

        "image_quality_score":
            quality_score,

        "dropout_percentage":
            100.0
            if local_dropout
            else 0.0,

        "warnings":
            warnings,
    }


# ============================================================
# Complete image analysis
# ============================================================

def analyze_sonar_image(image):
    """
    Perform complete image-level sonar analysis.

    This can be used before YOLO inference if required.
    """

    quality = calculate_image_quality(
        image
    )

    dropout = detect_data_dropouts(
        image
    )

    texture = calculate_texture_score(
        image
    )

    edge = calculate_edge_score(
        image
    )

    warnings = []

    if quality["quality_score"] < 40:

        warnings.append(
            "Low image quality"
        )

    if quality["contrast"] < 15:

        warnings.append(
            "Low image contrast"
        )

    if dropout["dropout_detected"]:

        warnings.append(
            "Possible image dropout or saturated region detected"
        )

    return {
        "image_quality":
            quality,

        "dropout_analysis":
            dropout,

        "texture_score":
            texture,

        "edge_score":
            edge,

        "warnings":
            warnings,

        "motion_metadata_available":
            False,

        "motion_note":
            (
                "True heave/pitch/roll correction requires "
                "original sonar navigation metadata."
            ),
    }
