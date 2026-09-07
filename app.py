import streamlit as st
from pathlib import Path
from PIL import Image
from ultralytics import YOLO

import json
import csv
import io
import time

import numpy as np
import pandas as pd

from geotag import (
    footprint_pixel_to_gps,
    valid_coordinate
)

from preprocess import (
    preprocess_with_analysis,
    TARGET_WIDTH,
    TARGET_HEIGHT
)

from sonar_analysis import (
    validate_detection
)


# ============================================================
# MarineDebrisAI
# AI-Powered Side-Scan Sonar Object Detection & Geotagging
# ============================================================


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "best.pt"

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MarineDebrisAI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 19px;
        margin-top: 0px;
        margin-bottom: 15px;
    }

    .anomaly-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #555;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌊 MarineDebrisAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Side-Scan Sonar Object Detection & Geotagging'
    '</div>',
    unsafe_allow_html=True
)

st.info(
    "MarineDebrisAI analyzes side-scan sonar imagery using "
    "AI-based object detection, image-quality analysis, "
    "anomaly validation and approximate geographic localization."
)


# ============================================================
# MODEL LOADING
# ============================================================

@st.cache_resource
def load_model():
    return YOLO(str(MODEL_PATH))


if not MODEL_PATH.exists():

    st.error(
        "❌ AI model not found.\n\n"
        f"Expected location:\n`{MODEL_PATH}`"
    )

    st.stop()


try:

    model = load_model()

except Exception as e:

    st.error(
        "❌ The AI model could not be loaded."
    )

    st.exception(e)

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Analysis Settings")

st.sidebar.markdown("### Detection")

confidence_threshold = st.sidebar.slider(
    "Minimum confidence",
    min_value=0.10,
    max_value=0.95,
    value=0.25,
    step=0.05
)

iou_threshold = st.sidebar.slider(
    "IoU threshold",
    min_value=0.10,
    max_value=0.90,
    value=0.45,
    step=0.05
)

st.sidebar.caption(
    "Increase confidence to reduce weak detections."
)

st.sidebar.divider()

st.sidebar.markdown("### Sonar Analysis")

st.sidebar.caption(
    "Enabled:"
)

st.sidebar.write(
    "• Resolution normalization"
)

st.sidebar.write(
    "• Adaptive contrast enhancement"
)

st.sidebar.write(
    "• Noise reduction"
)

st.sidebar.write(
    "• Image quality scoring"
)

st.sidebar.write(
    "• Possible dropout detection"
)

st.sidebar.write(
    "• Texture analysis"
)

st.sidebar.write(
    "• Edge analysis"
)

st.sidebar.write(
    "• Shadow-like evidence"
)

st.sidebar.divider()

st.sidebar.markdown("### Model")

st.sidebar.write(
    f"Model: `{MODEL_PATH.name}`"
)

st.sidebar.write(
    f"Confidence: `{confidence_threshold * 100:.0f}%`"
)

st.sidebar.write(
    f"IoU: `{iou_threshold:.2f}`"
)

st.sidebar.divider()

st.sidebar.caption(
    "True heave/pitch/roll correction requires original "
    "sonar navigation metadata."
)


# ============================================================
# GEOGRAPHIC FOOTPRINT
# ============================================================

st.header("🗺️ Survey Geographic Footprint")

st.write(
    "Enter the approximate geographic coverage represented "
    "by the uploaded sonar image."
)

geo_col1, geo_col2 = st.columns(2)

with geo_col1:

    latitude_min = st.number_input(
        "Minimum Latitude",
        value=17.000000,
        format="%.7f"
    )

    latitude_max = st.number_input(
        "Maximum Latitude",
        value=17.010000,
        format="%.7f"
    )

with geo_col2:

    longitude_min = st.number_input(
        "Minimum Longitude",
        value=78.000000,
        format="%.7f"
    )

    longitude_max = st.number_input(
        "Maximum Longitude",
        value=78.010000,
        format="%.7f"
    )


# ============================================================
# GEO VALIDATION
# ============================================================

coordinates_valid = all(
    [
        valid_coordinate(
            latitude_min,
            longitude_min
        ),
        valid_coordinate(
            latitude_max,
            longitude_max
        )
    ]
)

if not coordinates_valid:

    st.error(
        "❌ Invalid geographic coordinates."
    )

    st.stop()


if latitude_min >= latitude_max:

    st.warning(
        "⚠️ Minimum latitude must be smaller than maximum latitude."
    )

    st.stop()


if longitude_min >= longitude_max:

    st.warning(
        "⚠️ Minimum longitude must be smaller than maximum longitude."
    )

    st.stop()


st.caption(
    f"Survey footprint: "
    f"{latitude_min:.7f} → {latitude_max:.7f} latitude | "
    f"{longitude_min:.7f} → {longitude_max:.7f} longitude"
)

st.warning(
    "⚠️ GPS positions are approximate because this prototype "
    "uses the supplied image footprint. Accurate marine "
    "positioning requires GPS/INS/sonar navigation metadata."
)


# ============================================================
# IMAGE UPLOAD
# ============================================================

st.header("📡 Sonar Image Analysis")

uploaded_file = st.file_uploader(
    "Upload a side-scan sonar image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "tif",
        "tiff"
    ]
)


# ============================================================
# MAIN PROCESSING
# ============================================================

if uploaded_file is not None:

    # ========================================================
    # LOAD IMAGE
    # ========================================================

    try:

        original_image = Image.open(
            uploaded_file
        ).convert("RGB")

    except Exception as e:

        st.error(
            "❌ Unable to read the uploaded sonar image."
        )

        st.exception(e)

        st.stop()


    original_width, original_height = (
        original_image.size
    )


    # ========================================================
    # INPUT INFORMATION
    # ========================================================

    st.subheader("📷 Input Information")

    info1, info2, info3, info4 = st.columns(4)

    with info1:

        st.metric(
            "Width",
            f"{original_width}px"
        )

    with info2:

        st.metric(
            "Height",
            f"{original_height}px"
        )

    with info3:

        st.metric(
            "Confidence",
            f"{confidence_threshold * 100:.0f}%"
        )

    with info4:

        st.metric(
            "IoU",
            f"{iou_threshold:.2f}"
        )


    # ========================================================
    # ORIGINAL IMAGE
    # ========================================================

    st.subheader("Original Sonar Image")

    st.image(
        original_image,
        caption=uploaded_file.name,
        use_container_width=True
    )


    # ========================================================
    # PROCESSING PROGRESS
    # ========================================================

    progress = st.progress(
        0,
        text="Starting sonar analysis..."
    )

    start_time = time.perf_counter()


    # ========================================================
    # PREPROCESSING
    # ========================================================

    try:

        progress.progress(
            10,
            text="Analyzing sonar image quality..."
        )

        processed_image, preprocessing_analysis = (
            preprocess_with_analysis(
                original_image
            )
        )

        progress.progress(
            30,
            text="Enhancing contrast and reducing noise..."
        )

    except Exception as e:

        progress.empty()

        st.error(
            "❌ Sonar preprocessing failed."
        )

        st.exception(e)

        st.stop()


    # ========================================================
    # QUALITY DATA
    # ========================================================

    quality = preprocessing_analysis.get(
        "original_quality",
        {}
    )

    processed_quality = preprocessing_analysis.get(
        "processed_quality",
        {}
    )

    dropout_analysis = preprocessing_analysis.get(
        "dropout_analysis",
        {}
    )

    preprocessing_warnings = preprocessing_analysis.get(
        "warnings",
        []
    )


    # ========================================================
    # SONAR QUALITY
    # ========================================================

    st.subheader("🔊 Sonar Image Quality")

    quality1, quality2, quality3, quality4 = (
        st.columns(4)
    )

    with quality1:

        st.metric(
            "Quality Score",
            f"{quality.get('quality_score', 0):.1f}%"
        )

    with quality2:

        st.metric(
            "Contrast",
            f"{quality.get('contrast', 0):.1f}"
        )

    with quality3:

        st.metric(
            "Sharpness",
            f"{quality.get('sharpness', 0):.1f}"
        )

    with quality4:

        dropout_detected = dropout_analysis.get(
            "dropout_detected",
            False
        )

        st.metric(
            "Possible Dropout",
            "Yes" if dropout_detected else "No"
        )


    # ========================================================
    # QUALITY WARNINGS
    # ========================================================

    if preprocessing_warnings:

        for warning in preprocessing_warnings:

            st.warning(
                f"⚠️ {warning}"
            )

    else:

        st.success(
            "✅ No major image-quality warnings detected."
        )


    # ========================================================
    # PREPROCESSED IMAGE
    # ========================================================

    with st.expander(
        "🔧 View Preprocessed Sonar Image"
    ):

        st.image(
            processed_image,
            caption="Image used for AI inference",
            use_container_width=True
        )

        st.caption(
            f"Processing resolution: "
            f"{TARGET_WIDTH} × {TARGET_HEIGHT}px"
        )

        st.caption(
            f"Processed quality score: "
            f"{processed_quality.get('quality_score', 0):.1f}%"
        )


    # ========================================================
    # YOLO DETECTION
    # ========================================================

    try:

        progress.progress(
            50,
            text="Running AI object detection..."
        )

        results = model.predict(
            source=processed_image,
            conf=confidence_threshold,
            iou=iou_threshold,
            save=False,
            verbose=False
        )

        progress.progress(
            70,
            text="Validating detected anomalies..."
        )

    except Exception as e:

        progress.empty()

        st.error(
            "❌ AI detection failed."
        )

        st.exception(e)

        st.stop()


    # ========================================================
    # RESULT OBJECT
    # ========================================================

    result = results[0]


    # ========================================================
    # IMAGE TRANSFORMATION PARAMETERS
    # ========================================================

    scale = min(
        TARGET_WIDTH / original_width,
        TARGET_HEIGHT / original_height
    )

    resized_width = max(
        1,
        int(round(original_width * scale))
    )

    resized_height = max(
        1,
        int(round(original_height * scale))
    )

    pad_x = (
        TARGET_WIDTH - resized_width
    ) // 2

    pad_y = (
        TARGET_HEIGHT - resized_height
    ) // 2


    # ========================================================
    # DETECTION EXTRACTION
    # ========================================================

    detections = []


    if result.boxes is not None:

        number_of_boxes = len(
            result.boxes
        )

        for i in range(
            number_of_boxes
        ):

            # =================================================
            # CLASS
            # =================================================

            class_id = int(
                result.boxes.cls[i]
            )

            class_name = model.names.get(
                class_id,
                str(class_id)
            )


            # =================================================
            # MODEL CONFIDENCE
            # =================================================

            confidence = float(
                result.boxes.conf[i]
            )


            # =================================================
            # PROCESSED IMAGE BOX
            # =================================================

            box = result.boxes.xyxy[i].tolist()

            px1 = float(box[0])
            py1 = float(box[1])
            px2 = float(box[2])
            py2 = float(box[3])


            # =================================================
            # PROCESSED IMAGE CENTER
            # =================================================

            processed_center_x = (
                px1 + px2
            ) / 2.0

            processed_center_y = (
                py1 + py2
            ) / 2.0


            # =================================================
            # CONVERT BOX BACK TO ORIGINAL IMAGE
            # =================================================

            original_x1 = (
                px1 - pad_x
            ) / scale

            original_y1 = (
                py1 - pad_y
            ) / scale

            original_x2 = (
                px2 - pad_x
            ) / scale

            original_y2 = (
                py2 - pad_y
            ) / scale


            original_center_x = (
                processed_center_x - pad_x
            ) / scale

            original_center_y = (
                processed_center_y - pad_y
            ) / scale


            # =================================================
            # CLAMP ORIGINAL COORDINATES
            # =================================================

            original_x1 = max(
                0.0,
                min(
                    original_x1,
                    float(original_width)
                )
            )

            original_y1 = max(
                0.0,
                min(
                    original_y1,
                    float(original_height)
                )
            )

            original_x2 = max(
                0.0,
                min(
                    original_x2,
                    float(original_width)
                )
            )

            original_y2 = max(
                0.0,
                min(
                    original_y2,
                    float(original_height)
                )
            )

            original_center_x = max(
                0.0,
                min(
                    original_center_x,
                    float(original_width)
                )
            )

            original_center_y = max(
                0.0,
                min(
                    original_center_y,
                    float(original_height)
                )
            )


            # =================================================
            # DIMENSIONS
            # =================================================

            width_pixels = max(
                0.0,
                original_x2 - original_x1
            )

            height_pixels = max(
                0.0,
                original_y2 - original_y1
            )


            # =================================================
            # SONAR VALIDATION
            # =================================================

            try:

                validation = validate_detection(
                    np.asarray(
                        processed_image
                    ),
                    (
                        int(px1),
                        int(py1),
                        int(px2),
                        int(py2)
                    ),
                    confidence
                )

            except Exception as validation_error:

                validation = {
                    "model_confidence":
                        round(
                            confidence * 100.0,
                            2
                        ),

                    "anomaly_score":
                        round(
                            confidence * 100.0,
                            2
                        ),

                    "assessment":
                        (
                            "High"
                            if confidence >= 0.80
                            else
                            "Moderate"
                            if confidence >= 0.60
                            else
                            "Low"
                        ),

                    "shadow_score": 0.0,

                    "texture_score": 0.0,

                    "edge_score": 0.0,

                    "image_quality_score":
                        quality.get(
                            "quality_score",
                            0.0
                        ),

                    "dropout_percentage":
                        dropout_analysis.get(
                            "dropout_percentage",
                            0.0
                        ),

                    "warnings": [
                        "Advanced validation unavailable"
                    ]
                }


            # =================================================
            # CONFIDENCE LEVEL
            # =================================================

            if confidence >= 0.80:

                confidence_level = "High"

            elif confidence >= 0.60:

                confidence_level = "Moderate"

            else:

                confidence_level = "Low"


            # =================================================
            # ANOMALY SCORE
            # =================================================

            anomaly_score = float(
                validation.get(
                    "anomaly_score",
                    confidence * 100.0
                )
            )

            anomaly_assessment = validation.get(
                "assessment",
                confidence_level
            )


            # =====
