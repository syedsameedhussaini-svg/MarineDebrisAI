"""
MarineDebrisAI - Sonar Image Analysis Module

Provides image-based analysis for side-scan sonar imagery:
- Image quality assessment
- Possible data-dropout detection
- Local contrast analysis
- Texture analysis
- Edge/structure analysis
- Shadow-like region analysis
- Detection validation support

Important:
This module does NOT perform true INS/GPS-based heave, pitch, or roll
correction. That requires the original sonar/navigation metadata.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def _safe_float(value: float, default: float = 0.0) -> float:
    """Convert a value to a finite float."""
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    """Clamp a value to the range 0-1."""
    return float(np.clip(value, 0.0, 1.0))


def _to_gray(image: np.ndarray) -> np.ndarray:
    """Convert an image to grayscale safely."""
    if image is None:
        raise ValueError("Image is None.")

    if not isinstance(image, np.ndarray):
        image = np.asarray(image)

    if image.size == 0:
        raise ValueError("Image is empty.")

    if len(image.shape) == 2:
        gray = image
    elif image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return gray.astype(np.uint8)


# ---------------------------------------------------------------------
# Image quality
# ---------------------------------------------------------------------

def calculate_image_quality(image: np.ndarray) -> Dict[str, float]:
    """
    Calculate basic image-quality measurements.

    Returns:
        Dictionary containing:
        - brightness
        - contrast
        - sharpness
        - quality_score
    """
    gray = _to_gray(image)

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    # Variance of Laplacian is a common sharpness indicator.
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Normalize measurements into approximate 0-1 ranges.
    brightness_score = 1.0 - min(abs(brightness - 127.5) / 127.5, 1.0)

    contrast_score = _clip01(contrast / 64.0)

    # Sharpness can vary substantially between sonar datasets.
    sharpness_score = _clip01(sharpness / 500.0)

    quality_score = (
        0.35 * brightness_score
        + 0.40 * contrast_score
        + 0.25 * sharpness_score
    )

    return {
        "brightness": round(brightness, 3),
        "contrast": round(contrast, 3),
        "sharpness": round(sharpness, 3),
        "quality_score": round(quality_score * 100.0, 2),
    }


# ---------------------------------------------------------------------
# Dropout detection
# ---------------------------------------------------------------------

def detect_data_dropouts(
    image: np.ndarray,
    tile_size: int = 32,
) -> Dict[str, object]:
    """
    Detect suspicious image regions that may represent data dropout,
    saturation, dead pixels, or unusually uniform sonar regions.

    This is an image-quality indicator, NOT a definitive diagnosis of
    sonar data loss.
    """
    gray = _to_gray(image)

    height, width = gray.shape

    if height < tile_size or width < tile_size:
        return {
            "dropout_detected": False,
            "dropout_percentage": 0.0,
            "dropout_tiles": 0,
            "total_tiles": 0,
        }

    suspicious_tiles = 0
    total_tiles = 0

    for y in range(0, height - tile_size + 1, tile_size):
        for x in range(0, width - tile_size + 1, tile_size):
            tile = gray[y:y + tile_size, x:x + tile_size]

            tile_mean = float(np.mean(tile))
            tile_std = float(np.std(tile))

            # Extremely uniform dark/bright blocks can indicate
            # missing/saturated data or other acquisition artifacts.
            uniform = tile_std < 3.0
            extremely_dark = tile_mean < 3.0
            extremely_bright = tile_mean > 252.0

            if uniform and (extremely_dark or extremely_bright):
                suspicious_tiles += 1

            total_tiles += 1

    percentage = (
        100.0 * suspicious_tiles / total_tiles
        if total_tiles > 0
        else 0.0
    )

    return {
        "dropout_detected": bool(percentage >= 1.0),
        "dropout_percentage": round(percentage, 2),
        "dropout_tiles": suspicious_tiles,
        "total_tiles": total_tiles,
    }


# ---------------------------------------------------------------------
# Texture analysis
# ---------------------------------------------------------------------

def calculate_texture_score(image: np.ndarray) -> float:
    """
    Estimate local texture/variation.

    Higher values indicate stronger local intensity variation.
    This is not a semantic 'debris score'.
    """
    gray = _to_gray(image)

    # Local standard deviation.
    mean = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), 3)
    squared_mean = cv2.GaussianBlur(
        (gray.astype(np.float32) ** 2),
        (0, 0),
        3,
    )

    variance = np.maximum(squared_mean - mean ** 2, 0)
    local_std = np.sqrt(variance)

    score = float(np.mean(local_std))

    return round(_clip01(score / 32.0) * 100.0, 2)


# ---------------------------------------------------------------------
# Edge / structure analysis
# ---------------------------------------------------------------------

def calculate_edge_score(image: np.ndarray) -> float:
    """
    Calculate the proportion of pixels containing strong edges.
    """
    gray = _to_gray(image)

    edges = cv2.Canny(gray, 50, 150)

    edge_percentage = 100.0 * float(np.count_nonzero(edges)) / edges.size

    # Typical natural sonar imagery can have a broad range of edge
    # densities, so this is only an image descriptor.
    score = _clip01(edge_percentage / 20.0) * 100.0

    return round(score, 2)


# ---------------------------------------------------------------------
# Shadow-like analysis
# ---------------------------------------------------------------------

def analyze_shadow_like_region(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
) -> Dict[str, float]:
    """
    Look for a darker region immediately behind/beside a detected object.

    This is an image-based 'shadow-like evidence' measurement.

    It does NOT claim to identify a physically correct acoustic shadow.
    """
    gray = _to_gray(image)

    height, width = gray.shape

    x1, y1, x2, y2 = [int(v) for v in bbox]

    x1 = max(0, min(x1, width - 1))
    x2 = max(0, min(x2, width))
    y1 = max(0, min(y1, height - 1))
    y2 = max(0, min(y2, height))

    if x2 <= x1 or y2 <= y1:
        return {
            "shadow_score": 0.0,
            "object_mean": 0.0,
            "background_mean": 0.0,
            "shadow_mean": 0.0,
        }

    object_region = gray[y1:y2, x1:x2]

    if object_region.size == 0:
        return {
            "shadow_score": 0.0,
            "object_mean": 0.0,
            "background_mean": 0.0,
            "shadow_mean": 0.0,
        }

    object_mean = float(np.mean(object_region))

    # Estimate surrounding background.
    margin_x = max(5, int((x2 - x1) * 0.5))
    margin_y = max(5, int((y2 - y1) * 0.5))

    bx1 = max(0, x1 - margin_x)
    bx2 = min(width, x2 + margin_x)
    by1 = max(0, y1 - margin_y)
    by2 = min(height, y2 + margin_y)

    background_region = gray[by1:by2, bx1:bx2]

    if background_region.size == 0:
        background_mean = object_mean
    else:
        background_mean = float(np.mean(background_region))

    # Check a region immediately after the object in the horizontal
    # direction. This is a simple approximation because actual sonar
    # shadow direction depends on sonar geometry.
    shadow_width = max(5, int((x2 - x1) * 1.5))

    sx1 = x2
    sx2 = min(width, x2 + shadow_width)

    shadow_region = gray[y1:y2, sx1:sx2]

    if shadow_region.size == 0:
        shadow_mean = background_mean
    else:
        shadow_mean = float(np.mean(shadow_region))

    # A darker-than-background region gives stronger shadow-like evidence.
    darkness_difference = max(
        0.0,
        background_mean - shadow_mean
    )

    # Normalize.
    shadow_score = _clip01(darkness_difference / 60.0) * 100.0

    return {
        "shadow_score": round(shadow_score, 2),
        "object_mean": round(object_mean, 2),
        "background_mean": round(background_mean, 2),
        "shadow_mean": round(shadow_mean, 2),
    }


# ---------------------------------------------------------------------
# Detection validation
# ---------------------------------------------------------------------

def validate_detection(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    model_confidence: float,
) -> Dict[str, object]:
    """
    Combine YOLO confidence with image-based supporting evidence.

    The resulting anomaly score is deliberately conservative.
    Model confidence remains the dominant factor.
    """
    quality = calculate_image_quality(image)

    shadow = analyze_shadow_like_region(
        image,
        bbox,
    )

    texture_score = calculate_texture_score(image)
    edge_score = calculate_edge_score(image)

    model_confidence = _clip01(_safe_float(model_confidence))

    quality_score = quality["quality_score"] / 100.0
    shadow_score = shadow["shadow_score"] / 100.0
    texture_normalized = texture_score / 100.0
    edge_normalized = edge_score / 100.0

    # YOLO confidence is deliberately weighted highest.
    anomaly_score = (
        0.65 * model_confidence
        + 0.15 * shadow_score
        + 0.10 * quality_score
        + 0.05 * texture_normalized
        + 0.05 * edge_normalized
    )

    anomaly_score = _clip01(anomaly_score) * 100.0

    if anomaly_score >= 80:
        assessment = "High"
    elif anomaly_score >= 60:
        assessment = "Moderate"
    else:
        assessment = "Low"

    warnings = []

    if quality["quality_score"] < 40:
        warnings.append("Low overall image quality")

    dropout = detect_data_dropouts(image)

    if dropout["dropout_detected"]:
        warnings.append(
            "Possible data dropout or saturated region detected"
        )

    if shadow["shadow_score"] < 15:
        warnings.append(
            "Weak shadow-like evidence"
        )

    return {
        "model_confidence": round(model_confidence * 100.0, 2),
        "anomaly_score": round(anomaly_score, 2),
        "assessment": assessment,
        "shadow_score": shadow["shadow_score"],
        "texture_score": texture_score,
        "edge_score": edge_score,
        "image_quality_score": quality["quality_score"],
        "dropout_percentage": dropout["dropout_percentage"],
        "warnings": warnings,
    }


# ---------------------------------------------------------------------
# Complete image analysis
# ---------------------------------------------------------------------

def analyze_sonar_image(image: np.ndarray) -> Dict[str, object]:
    """
    Perform complete image-level sonar analysis.

    This function can be called before YOLO inference.
    """
    quality = calculate_image_quality(image)
    dropout = detect_data_dropouts(image)
    texture = calculate_texture_score(image)
    edge = calculate_edge_score(image)

    warnings = []

    if quality["quality_score"] < 40:
        warnings.append("Low image quality")

    if quality["contrast"] < 15:
        warnings.append("Low image contrast")

    if dropout["dropout_detected"]:
        warnings.append(
            "Possible image dropout or saturated region detected"
        )

    return {
        "image_quality": quality,
        "dropout_analysis": dropout,
        "texture_score": texture,
        "edge_score": edge,
        "warnings": warnings,
        "motion_metadata_available": False,
        "motion_note": (
            "True heave/pitch/roll correction requires "
            "original sonar navigation metadata."
        ),
      }
