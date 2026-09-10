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


# ============================================================
# MarineDebrisAI
# AI-Powered Side-Scan Sonar Object Detection
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
    }

    .metric-card {
        padding: 10px;
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

st.write("")

st.info(
    "MarineDebrisAI analyzes side-scan sonar imagery to identify "
    "potential man-made marine anomalies, estimate their geographic "
    "locations, assess image quality, and generate structured "
    "anomaly reports."
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
    "Higher confidence thresholds reduce low-confidence detections."
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

st.sidebar.markdown("### Sonar Processing")

st.sidebar.success(
    "✓ Resolution normalization"
)

st.sidebar.success(
    "✓ Adaptive contrast enhancement"
)

st.sidebar.success(
    "✓ Noise reduction"
)

st.sidebar.success(
    "✓ Image quality analysis"
)

st.sidebar.success(
    "✓ Possible dropout detection"
)

st.sidebar.caption(
    "True heave/pitch/roll correction requires "
    "original sonar navigation metadata."
)


# ============================================================
# GEOGRAPHIC FOOTPRINT
# ============================================================

st.header("🗺️ Survey Geographic Footprint")

st.write(
    "Define the approximate geographic coverage of the sonar image. "
    "Detected pixel locations will be converted into estimated "
    "latitude and longitude coordinates."
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


# ============================================================
# GEO INFORMATION
# ============================================================

st.caption(
    f"Survey area: "
    f"{latitude_min:.7f} → {latitude_max:.7f} latitude, "
    f"{longitude_min:.7f} → {longitude_max:.7f} longitude"
)

st.warning(
    "⚠️ Geographic coordinates are approximate and are derived "
    "from the supplied image footprint. Accurate marine positioning "
    "requires actual GPS/INS/sonar navigation metadata."
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
# IMAGE PROCESSING
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
            "❌ Unable to read the uploaded image."
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
    # PREPROCESSING
    # ========================================================

    progress = st.progress(
        0,
        text="Preparing sonar analysis..."
    )

    total_start = time.perf_counter()


    try:

        progress.progress(
            15,
            text="Analyzing sonar image quality..."
        )

        processed_image, preprocessing_analysis = (
            preprocess_with_analysis(
                original_image
            )
        )

        progress.progress(
            35,
            text="Preprocessing sonar imagery..."
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

    quality = preprocessing_analysis[
        "original_quality"
    ]

    processed_quality = preprocessing_analysis[
        "processed_quality"
    ]

    dropout_analysis = preprocessing_analysis[
        "dropout_analysis"
    ]

    preprocessing_warnings = (
        preprocessing_analysis[
            "warnings"
        ]
    )


    # ========================================================
    # SONAR QUALITY
    # ========================================================

    st.subheader(
        "🔊 Sonar Image Quality"
    )

    quality1, quality2, quality3, quality4 = (
        st.columns(4)
    )


    with quality1:

        st.metric(
            "Quality Score",
            f"{quality['quality_score']:.1f}%"
        )


    with quality2:

        st.metric(
            "Contrast",
            f"{quality['contrast']:.1f}"
        )


    with quality3:

        st.metric(
            "Sharpness",
            f"{quality['sharpness']:.1f}"
        )


    with quality4:

        st.metric(
            "Possible Dropout",
            (
                "Yes"
                if dropout_analysis[
                    "dropout_detected"
                ]
                else "No"
            )
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
            caption="Preprocessed image used for AI inference",
            use_container_width=True
        )

        st.caption(
            f"Processing resolution: "
            f"{TARGET_WIDTH} × {TARGET_HEIGHT}px"
        )

        st.caption(
            f"Processed quality score: "
            f"{processed_quality['quality_score']:.1f}%"
        )


    # ========================================================
    # YOLO DETECTION
    # ========================================================

    try:

        progress.progress(
            55,
            text="Running YOLO object detection..."
        )

        detection_start = time.perf_counter()

        results = model.predict(
            source=processed_image,
            conf=confidence_threshold,
            iou=iou_threshold,
            save=False,
            verbose=False
        )

        detection_time = (
            time.perf_counter()
            - detection_start
        )

        progress.progress(
            85,
            text="Preparing detection results..."
        )

    except Exception as e:

        progress.empty()

        st.error(
            "❌ AI detection failed."
        )

        st.exception(e)

        st.stop()


    # ========================================================
    # RESULT
    # ========================================================

    result = results[0]


    # ========================================================
    # COORDINATE TRANSFORMATION
    # ========================================================

    scale = min(
        TARGET_WIDTH / original_width,
        TARGET_HEIGHT / original_height
    )

    resized_width = max(
        1,
        int(
            round(
                original_width * scale
            )
        )
    )

    resized_height = max(
        1,
        int(
            round(
                original_height * scale
            )
        )
    )

    pad_x = (
        TARGET_WIDTH
        - resized_width
    ) // 2

    pad_y = (
        TARGET_HEIGHT
        - resized_height
    ) // 2


    # ========================================================
    # DETECTION EXTRACTION
    # ========================================================

    detections = []


    if result.boxes is not None:

        for i in range(
            len(result.boxes)
        ):

            # ------------------------------------------------
            # CLASS
            # ------------------------------------------------

            class_id = int(
                result.boxes.cls[i]
            )

            class_name = model.names[
                class_id
            ]


            # ------------------------------------------------
            # MODEL CONFIDENCE
            # ------------------------------------------------

            confidence = float(
                result.boxes.conf[i]
            )


            # ------------------------------------------------
            # PROCESSED BOX
            # ------------------------------------------------

            px1, py1, px2, py2 = (
                result.boxes.xyxy[i].tolist()
            )


            # ------------------------------------------------
            # PROCESSED CENTER
            # ------------------------------------------------

            processed_center_x = (
                px1 + px2
            ) / 2.0

            processed_center_y = (
                py1 + py2
            ) / 2.0


            # ------------------------------------------------
            # CONVERT TO ORIGINAL IMAGE
            # ------------------------------------------------

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
                processed_center_x
                - pad_x
            ) / scale

            original_center_y = (
                processed_center_y
                - pad_y
            ) / scale


            # ------------------------------------------------
            # CLAMP VALUES
            # ------------------------------------------------

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


            # ------------------------------------------------
            # DIMENSIONS
            # ------------------------------------------------

            width_pixels = (
                original_x2
                - original_x1
            )

            height_pixels = (
                original_y2
                - original_y1
            )


            # =================================================
            # LIGHTWEIGHT ANOMALY SCORE
            # =================================================
            #
            # We deliberately avoid expensive per-object
            # full-image analysis.
            #

            quality_factor = (
                quality["quality_score"]
                / 100.0
            )

            anomaly_score = (
                0.85 * confidence
                + 0.15 * quality_factor
            )

            anomaly_score = max(
                0.0,
                min(
                    anomaly_score,
                    1.0
                )
            )

            anomaly_score_percent = (
                anomaly_score * 100.0
            )


            if anomaly_score_percent >= 80:

                anomaly_assessment = "High"

            elif anomaly_score_percent >= 60:

                anomaly_assessment = "Moderate"

            else:

                anomaly_assessment = "Low"


            # ------------------------------------------------
            # CONFIDENCE LEVEL
            # ------------------------------------------------

            if confidence >= 0.80:

                confidence_level = "High"

            elif confidence >= 0.60:

                confidence_level = "Moderate"

            else:

                confidence_level = "Low"


            # =================================================
            # GEOTAG
            # =================================================

            latitude, longitude = (
                footprint_pixel_to_gps(
                    original_center_x,
                    original_center_y,
                    original_width,
                    original_height,
                    latitude_min,
                    latitude_max,
                    longitude_min,
                    longitude_max
                )
            )


            # =================================================
            # DETECTION OBJECT
            # =================================================

            detections.append(
                {
                    "image":
                        uploaded_file.name,

                    "classification":
                        class_name,

                    "confidence":
                        round(
                            confidence * 100.0,
                            2
                        ),

                    "confidence_level":
                        confidence_level,

                    "anomaly_score":
                        round(
                            anomaly_score_percent,
                            2
                        ),

                    "anomaly_assessment":
                        anomaly_assessment,

                    "bounding_box":
                        {
                            "x1":
                                round(
                                    original_x1,
                                    2
                                ),

                            "y1":
                                round(
                                    original_y1,
                                    2
                                ),

                            "x2":
                                round(
                                    original_x2,
                                    2
                                ),

                            "y2":
                                round(
                                    original_y2,
                                    2
                                )
                        },

                    "center_pixel":
                        {
                            "x":
                                round(
                                    original_center_x,
                                    2
                                ),

                            "y":
                                round(
                                    original_center_y,
                                    2
                                )
                        },

                    "width_pixels":
                        round(
                            width_pixels,
                            2
                        ),

                    "height_pixels":
                        round(
                            height_pixels,
                            2
                        ),

                    "latitude":
                        latitude,

                    "longitude":
                        longitude
                }
            )


    # ========================================================
    # ANNOTATED IMAGE
    # ========================================================

    annotated = result.plot()


    # ========================================================
    # FINISH PROCESSING
    # ========================================================

    progress.progress(
        100,
        text="Analysis complete."
    )

    time.sleep(0.15)

    progress.empty()


    total_processing_time = (
        time.perf_counter()
        - total_start
    )


    # ========================================================
    # DETECTION SUMMARY
    # ========================================================

    st.header(
        "🔎 Detection Summary"
    )


    total_detections = len(
        detections
    )


    high_count = sum(
        1
        for d in detections
        if d["confidence_level"] == "High"
    )


    moderate_count = sum(
        1
        for d in detections
        if d["confidence_level"] == "Moderate"
    )


    low_count = sum(
        1
        for d in detections
        if d["confidence_level"] == "Low"
    )


    if detections:

        average_confidence = (
            sum(
                d["confidence"]
                for d in detections
            )
            / len(detections)
        )

        highest_confidence = max(
            d["confidence"]
            for d in detections
        )

        highest_anomaly_score = max(
            d["anomaly_score"]
            for d in detections
        )

    else:

        average_confidence = 0.0

        highest_confidence = 0.0

        highest_anomaly_score = 0.0


    summary1, summary2, summary3, summary4 = (
        st.columns(4)
    )


    with summary1:

        st.metric(
            "Objects Detected",
            total_detections
        )


    with summary2:

        st.metric(
            "Highest Confidence",
            f"{highest_confidence:.1f}%"
        )


    with summary3:

        st.metric(
            "Highest Anomaly Score",
            f"{highest_anomaly_score:.1f}%"
        )


    with summary4:

        st.metric(
            "Total Processing",
            f"{total_processing_time:.2f}s"
        )


    if detections:

        st.caption(
            f"High: {high_count}  |  "
            f"Moderate: {moderate_count}  |  "
            f"Low: {low_count}  |  "
            f"YOLO inference: {detection_time:.2f}s"
        )


    # ========================================================
    # VISUAL RESULTS
    # ========================================================

    st.header(
        "🎯 AI Detection Results"
    )


    result_col1, result_col2 = (
        st.columns(
            [1.6, 1]
        )
    )


    with result_col1:

        st.image(
            annotated,
            caption=(
                "AI Detection — Bounding Boxes"
            ),
            use_container_width=True
        )


    with result_col2:

        if detections:

            st.subheader(
                "Detected Anomalies"
            )

            for number, detection in enumerate(
                detections,
                1
            ):

                st.markdown(
                    f"### {number}. "
                    f"{detection['classification']}"
                )

                st.write(
                    f"Model confidence: "
                    f"**{detection['confidence']:.2f}%**"
                )

                st.write(
                    f"Confidence level: "
                    f"**{detection['confidence_level']}**"
                )

                st.write(
                    f"Anomaly score: "
                    f"**{detection['anomaly_score']:.2f}%**"
                )

                st.write(
                    f"Assessment: "
                    f"**{detection['anomaly_assessment']}**"
                )

                st.write(
                    f"Estimated GPS: "
                    f"**{detection['latitude']}, "
                    f"{detection['longitude']}**"
                )

                st.write(
                    f"Bounding size: "
                    f"**{detection['width_pixels']} × "
                    f"{detection['height_pixels']} px**"
                )

                st.divider()

        else:

            st.success(
                "No potential anomalies were detected "
                "above the selected confidence threshold."
            )


    # ========================================================
    # STRUCTURED ANOMALY REPORT
    # ========================================================

    st.header(
        "📊 Structured Anomaly Report"
    )


    if detections:

        table_rows = []

        for number, detection in enumerate(
            detections,
            1
        ):

            table_rows.append(
                {
                    "#":
                        number,

                    "Classification":
                        detection[
                            "classification"
                        ],

                    "Confidence (%)":
                        detection[
                            "confidence"
                        ],

                    "Confidence Level":
                        detection[
                            "confidence_level"
                        ],

                    "Anomaly Score (%)":
                        detection[
                            "anomaly_score"
                        ],

                    "Assessment":
                        detection[
                            "anomaly_assessment"
                        ],

                    "Width (px)":
                        detection[
                            "width_pixels"
                        ],

                    "Height (px)":
                        detection[
                            "height_pixels"
                        ],

                    "Latitude":
                        detection[
                            "latitude"
                        ],

                    "Longitude":
                        detection[
                            "longitude"
                        ]
                }
            )


        dataframe = pd.DataFrame(
            table_rows
        )


        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No anomaly records available."
        )


    # ========================================================
    # MAP
    # ========================================================

    if detections:

        st.header(
            "🗺️ Detected Anomaly Locations"
        )

        map_rows = []

        for detection in detections:

            map_rows.append(
                {
                    "latitude":
                        detection[
                            "latitude"
                        ],

                    "longitude":
                        detection[
                            "longitude"
                        ]
                }
            )


        map_dataframe = pd.DataFrame(
            map_rows
        )


        st.map(
            map_dataframe,
            latitude="latitude",
            longitude="longitude",
            use_container_width=True
        )


        st.caption(
            "Map points represent estimated anomaly centers "
            "derived from the supplied survey footprint."
        )


    # ========================================================
    # JSON REPORT
    # ========================================================

    json_data = json.dumps(
        {
            "project":
                "MarineDebrisAI",

            "image":
                uploaded_file.name,

            "image_dimensions":
                {
                    "width":
                        original_width,

                    "height":
                        original_height
                },

            "survey_footprint":
                {
                    "latitude_min":
                        latitude_min,

                    "latitude_max":
                        latitude_max,

                    "longitude_min":
                        longitude_min,

                    "longitude_max":
                        longitude_max
                },

            "processing":
                {
                    "processing_resolution":
                        f"{TARGET_WIDTH}x{TARGET_HEIGHT}",

                    "image_quality":
                        quality,

                    "dropout_analysis":
                        dropout_analysis,

                    "total_processing_seconds":
                        round(
                            total_processing_time,
                            3
                        ),

                    "yolo_inference_seconds":
                        round(
                            detection_time,
                            3
                        )
                },

            "detections":
                detections,

            "limitations":
                [
                    "Geographic coordinates are approximate.",

                    "Actual GPS/INS/sonar navigation metadata "
                    "was not available.",

                    "True heave, pitch and roll correction "
                    "is therefore not performed.",

                    "Dropout detection is image-based and "
                    "does not represent definitive sonar "
                    "acquisition-data loss detection."
                ]
        },
        indent=4
    )


    # ========================================================
    # CSV REPORT
    # ========================================================

    csv_buffer = io.StringIO()

    fieldnames = [
        "image",
        "classification",
        "confidence_percent",
        "confidence_level",
        "anomaly_score_percent",
        "anomaly_assessment",
        "center_x",
        "center_y",
        "x1",
        "y1",
        "x2",
        "y2",
        "width_pixels",
        "height_pixels",
        "latitude",
        "longitude"
    ]


    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=fieldnames
    )


    writer.writeheader()


    for detection in detections:

        writer.writerow(
            {
                "image":
                    detection[
                        "image"
                    ],

                "classification":
                    detection[
                        "classification"
                    ],

                "confidence_percent":
                    detection[
                        "confidence"
                    ],

                "confidence_level":
                    detection[
                        "confidence_level"
                    ],

                "anomaly_score_percent":
                    detection[
                        "anomaly_score"
                    ],

                "anomaly_assessment":
                    detection[
                        "anomaly_assessment"
                    ],

                "center_x":
                    detection[
                        "center_pixel"
                    ][
                        "x"
                    ],

                "center_y":
                    detection[
                        "center_pixel"
                    ][
                        "y"
                    ],

                "x1":
                    detection[
                        "bounding_box"
                    ][
                        "x1"
                    ],

                "y1":
                    detection[
                        "bounding_box"
                    ][
                        "y1"
                    ],

                "x2":
                    detection[
                        "bounding_box"
                    ][
                        "x2"
                    ],

                "y2":
                    detection[
                        "bounding_box"
                    ][
                        "y2"
                    ],

                "width_pixels":
                    detection[
                        "width_pixels"
                    ],

                "height_pixels":
                    detection[
                        "height_pixels"
                    ],

                "latitude":
                    detection[
                        "latitude"
                    ],

                "longitude":
                    detection[
                        "longitude"
                    ]
            }
        )


    csv_data = (
        csv_buffer.getvalue()
    )


    # ========================================================
    # DOWNLOAD REPORTS
    # ========================================================

    st.header(
        "📥 Download Reports"
    )


    download_col1, download_col2 = (
        st.columns(2)
    )


    with download_col1:

        st.download_button(
            label="📄 Download JSON Report",

            data=json_data,

            file_name="detection_report.json",

            mime="application/json",

            use_container_width=True
        )


    with download_col2:

        st.download_button(
            label="📊 Download CSV Report",

            data=csv_data,

            file_name="anomaly_report.csv",

            mime="text/csv",

            use_container_width=True
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    if detections:

        st.success(
            f"✅ Analysis complete — "
            f"{len(detections)} potential anomaly(s) detected."
        )

    else:

        st.success(
            "✅ Analysis complete — "
            "no potential anomalies detected."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MarineDebrisAI | AI-assisted side-scan sonar anomaly "
    "detection, confidence scoring and approximate geospatial "
    "localization"
)
