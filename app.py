import streamlit as st
from pathlib import Path
from PIL import Image
from ultralytics import YOLO
import json
import csv
import io
import time
import pandas as pd

from geotag import footprint_pixel_to_gps, valid_coordinate

from preprocess import (
    preprocess_with_analysis,
    TARGET_WIDTH,
    TARGET_HEIGHT
)

from sonar_analysis import validate_detection


# ============================================================
# MarineDebrisAI
# AI-Powered Side-Scan Sonar Object Detection & Geotagging
# ============================================================


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "best.pt"

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="MarineDebrisAI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------------------
# CUSTOM CSS
# ------------------------------------------------------------

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

    .info-box {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #444;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# MODEL LOADING
# ------------------------------------------------------------

@st.cache_resource
def load_model():
    return YOLO(str(MODEL_PATH))


if not MODEL_PATH.exists():

    st.error(
        f"❌ AI model not found.\n\n"
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


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

st.sidebar.title("⚙️ Analysis Settings")

st.sidebar.markdown(
    "### Detection"
)

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

st.sidebar.markdown(
    "### Model"
)

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

st.sidebar.markdown(
    "### Sonar Analysis"
)

st.sidebar.caption(
    "Image-based quality, dropout and anomaly-evidence "
    "analysis is enabled."
)

st.sidebar.caption(
    "True heave/pitch/roll correction requires original "
    "sonar navigation metadata."
)


# ------------------------------------------------------------
# GEOGRAPHIC FOOTPRINT
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# GEO VALIDATION
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# GEOGRAPHIC INFORMATION
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# IMAGE UPLOAD
# ------------------------------------------------------------

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
# PROCESS IMAGE
# ============================================================

if uploaded_file is not None:

    # --------------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # IMAGE INFORMATION
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # ORIGINAL IMAGE
    # --------------------------------------------------------

    st.subheader("Original Sonar Image")

    st.image(
        original_image,
        caption=uploaded_file.name,
        use_container_width=True
    )


    # ========================================================
    # SONAR PREPROCESSING
    # ========================================================

    progress = st.progress(
        0,
        text="Preparing sonar analysis..."
    )

    start_time = time.perf_counter()

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
            30,
            text="Enhancing and filtering sonar imagery..."
        )

        time.sleep(0.1)

    except Exception as e:

        progress.empty()

        st.error(
            "❌ Sonar preprocessing failed."
        )

        st.exception(e)

        st.stop()


    # --------------------------------------------------------
    # IMAGE QUALITY RESULTS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # PREPROCESSING INFORMATION
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # QUALITY WARNINGS
    # --------------------------------------------------------

    if preprocessing_warnings:

        for warning in preprocessing_warnings:

            st.warning(
                f"⚠️ {warning}"
            )

    else:

        st.success(
            "✅ No major image-quality warnings detected."
        )


    # --------------------------------------------------------
    # PROCESSED IMAGE
    # --------------------------------------------------------

    with st.expander(
        "🔧 View Preprocessed Sonar Image"
    ):

        st.image(
            processed_image,
            caption=(
                "Preprocessed image used for AI inference"
            ),
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
            50,
            text="Running YOLO object detection..."
        )

        results = model.predict(
            source=processed_image,
            conf=confidence_threshold,
            iou=iou_threshold,
            save=False,
            verbose=False
        )

        progress.progress(
            75,
            text="Validating detected anomalies..."
        )

    except Exception as e:

        progress.empty()

        st.error(
            "❌ AI detection failed."
        )

        st.exception(e)

        st.stop()


    result = results[0]


    # ========================================================
    # DETECTION EXTRACTION
    # ========================================================

    detections = []


    # --------------------------------------------------------
    # Preprocessing transformation values
    #
    # Original image was resized to fit inside 1024x1024
    # while preserving aspect ratio.
    #
    # YOLO works on the processed 1024x1024 image.
    # We therefore convert detection pixels back to the
    # ORIGINAL image coordinate system before geotagging.
    # --------------------------------------------------------

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


    if result.boxes is not None:

        for i in range(
            len(result.boxes)
        ):

            # ------------------------------------------------
            # MODEL CLASS
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
            # PROCESSED-IMAGE BOUNDING BOX
            # ------------------------------------------------

            px1, py1, px2, py2 = (
                result.boxes.xyxy[i].tolist()
            )


            # ------------------------------------------------
            # CENTER IN PROCESSED IMAGE
            # ------------------------------------------------

            processed_center_x = (
                px1 + px2
            ) / 2.0

            processed_center_y = (
                py1 + py2
            ) / 2.0


            # ------------------------------------------------
            # CONVERT PROCESSED PIXELS BACK TO ORIGINAL IMAGE
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
                processed_center_x - pad_x
            ) / scale

            original_center_y = (
                processed_center_y - pad_y
            ) / scale


            # ------------------------------------------------
            # CLAMP TO ORIGINAL IMAGE
            # ------------------------------------------------

            original_x1 = max(
                0.0,
                min(
                    original_x1,
                    original_width
                )
            )

            original_y1 = max(
                0.0,
                min(
                    original_y1,
                    original_height
                )
            )

            original_x2 = max(
                0.0,
                min(
                    original_x2,
                    original_width
                )
            )

            original_y2 = max(
                0.0,
                min(
                    original_y2,
                    original_height
                )
            )

            original_center_x = max(
                0.0,
                min(
                    original_center_x,
                    original_width
                )
            )

            original_center_y = max(
                0.0,
                min(
                    original_center_y,
                    original_height
                )
            )


            # ------------------------------------------------
            # WIDTH / HEIGHT
            # ------------------------------------------------

            width_pixels = (
                original_x2 - original_x1
            )

            height_pixels = (
                original_y2 - original_y1
            )


            # ------------------------------------------------
            # SONAR EVIDENCE / VALIDATION
            #
            # Analysis is performed around the detected
            # bounding box in the processed sonar image.
            # ------------------------------------------------

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


            # ------------------------------------------------
            # CONFIDENCE LEVEL
            # ------------------------------------------------

            if confidence >= 0.80:

                confidence_level = "High"

            elif confidence >= 0.60:

                confidence_level = "Moderate"

            else:

                confidence_level = "Low"


            # ------------------------------------------------
            # ANOMALY ASSESSMENT
            # ------------------------------------------------

            anomaly_score = validation[
                "anomaly_score"
            ]

            anomaly_assessment = validation[
                "assessment"
            ]


            # ------------------------------------------------
            # GEOTAG
            #
            # IMPORTANT:
            # We use ORIGINAL image coordinates here because
            # the geographic footprint corresponds to the
            # uploaded image rather than the 1024x1024
            # padded processing canvas.
            # ------------------------------------------------

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


            # ------------------------------------------------
            # DETECTION OBJECT
            # ------------------------------------------------

            detections.append(

                {
                    "image":
                        uploaded_file.name,

                    "classification":
                        class_name,

                    "confidence":
                        round(
                            confidence * 100,
                            2
                        ),

                    "confidence_level":
                        confidence_level,

                    "anomaly_score":
                        round(
                            anomaly_score,
                            2
                        ),

                    "anomaly_assessment":
                        anomaly_assessment,

                    "validation":
                        {
                            "shadow_score":
                                validation[
             
