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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    "locations, and generate structured anomaly reports."
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
        valid_coordinate(latitude_min, longitude_min),
        valid_coordinate(latitude_max, longitude_max)
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


# ------------------------------------------------------------
# PROCESS IMAGE
# ------------------------------------------------------------

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


    image_width, image_height = (
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
            f"{image_width}px"
        )

    with info2:

        st.metric(
            "Height",
            f"{image_height}px"
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


    # --------------------------------------------------------
    # DETECTION
    # --------------------------------------------------------

    progress = st.progress(
        0,
        text="Preparing AI analysis..."
    )

    start_time = time.perf_counter()


    try:

        progress.progress(
            25,
            text="Loading sonar image..."
        )

        time.sleep(0.1)

        progress.progress(
            50,
            text="Running YOLO object detection..."
        )

        results = model.predict(
            source=original_image,
            conf=confidence_threshold,
            iou=iou_threshold,
            save=False,
            verbose=False
        )

        progress.progress(
            85,
            text="Processing detections..."
        )

    except Exception as e:

        progress.empty()

        st.error(
            "❌ AI detection failed."
        )

        st.exception(e)

        st.stop()


    processing_time = (
        time.perf_counter() - start_time
    )

    progress.progress(
        100,
        text="Analysis complete."
    )

    time.sleep(0.2)

    progress.empty()


    result = results[0]


    # --------------------------------------------------------
    # DETECTION EXTRACTION
    # --------------------------------------------------------

    detections = []


    if result.boxes is not None:

        for i in range(
            len(result.boxes)
        ):

            class_id = int(
                result.boxes.cls[i]
            )

            confidence = float(
                result.boxes.conf[i]
            )

            x1, y1, x2, y2 = (
                result.boxes.xyxy[i].tolist()
            )


            # ----------------------------------------------
            # CENTER PIXEL
            # ----------------------------------------------

            center_x = (
                x1 + x2
            ) / 2

            center_y = (
                y1 + y2
            ) / 2


            # ----------------------------------------------
            # GEOTAG
            # ----------------------------------------------

            latitude, longitude = (
                footprint_pixel_to_gps(
                    center_x,
                    center_y,
                    image_width,
                    image_height,
                    latitude_min,
                    latitude_max,
                    longitude_min,
                    longitude_max
                )
            )


            # ----------------------------------------------
            # CLASS
            # ----------------------------------------------

            class_name = model.names[
                class_id
            ]


            # ----------------------------------------------
            # DIMENSIONS
            # ----------------------------------------------

            width_pixels = (
                x2 - x1
            )

            height_pixels = (
                y2 - y1
            )


            # ----------------------------------------------
            # CONFIDENCE LEVEL
            # ----------------------------------------------

            if confidence >= 0.80:

                confidence_level = "High"

            elif confidence >= 0.60:

                confidence_level = "Moderate"

            else:

                confidence_level = "Low"


            # ----------------------------------------------
            # DETECTION OBJECT
            # ----------------------------------------------

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

                    "bounding_box":
                        {
                            "x1":
                                round(x1, 2),

                            "y1":
                                round(y1, 2),

                            "x2":
                                round(x2, 2),

                            "y2":
                                round(y2, 2)
                        },

                    "center_pixel":
                        {
                            "x":
                                round(center_x, 2),

                            "y":
                                round(center_y, 2)
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


    # --------------------------------------------------------
    # ANNOTATED IMAGE
    # --------------------------------------------------------

    annotated = result.plot()


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.header("🔎 Detection Summary")


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

        average_confidence = sum(
            d["confidence"]
            for d in detections
        ) / len(detections)

        highest_confidence = max(
            d["confidence"]
            for d in detections
        )

    else:

        average_confidence = 0
        highest_confidence = 0


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
            "Average Confidence",
            f"{average_confidence:.1f}%"
        )


    with summary4:

        st.metric(
            "Processing Time",
            f"{processing_time:.2f}s"
        )


    # --------------------------------------------------------
    # CONFIDENCE BREAKDOWN
    # --------------------------------------------------------

    if detections:

        st.caption(
            f"High: {high_count}  |  "
            f"Moderate: {moderate_count}  |  "
            f"Low: {low_count}"
        )


    # --------------------------------------------------------
    # VISUAL RESULTS
    # --------------------------------------------------------

    st.header("🎯 AI Detection Results")


    result_col1, result_col2 = (
        st.columns(
            [1.6, 1]
        )
    )


    with result_col1:

        st.image(
            annotated,
            caption="AI Detection — Bounding Boxes",
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
                    f"**{number}. "
                    f"{detection['classification']}**"
                )

                st.write(
                    f"Confidence: "
                    f"**{detection['confidence']}%**"
                )

                st.write(
                    f"Level: "
                    f"**{detection['confidence_level']}**"
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


    # --------------------------------------------------------
    # STRUCTURED TABLE
    # --------------------------------------------------------

    st.header("📊 Structured Anomaly Report")


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
                        detection["classification"],

                    "Confidence (%)":
                        detection["confidence"],

                    "Level":
                        detection["confidence_level"],

                    "Width (px)":
                        detection["width_pixels"],

                    "Height (px)":
                        detection["height_pixels"],

                    "Latitude":
                        detection["latitude"],

                    "Longitude":
                        detection["longitude"]
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


    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    if detections:

        st.header("🗺️ Detected Anomaly Locations")

        map_rows = []

        for detection in detections:

            map_rows.append(
                {
                    "latitude":
                        detection["latitude"],

                    "longitude":
                        detection["longitude"]
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


    # --------------------------------------------------------
    # JSON REPORT
    # --------------------------------------------------------

    json_data = json.dumps(
        detections,
        indent=4
    )


    json_path = (
        OUTPUT_DIR /
        "detection_report.json"
    )


    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            json_data
        )


    # --------------------------------------------------------
    # CSV REPORT
    # --------------------------------------------------------

    csv_buffer = io.StringIO()


    fieldnames = [

        "image",

        "classification",

        "confidence_percent",

        "confidence_level",

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
                    detection["image"],

                "classification":
                    detection["classification"],

                "confidence_percent":
                    detection["confidence"],

                "confidence_level":
                    detection["confidence_level"],

                "center_x":
                    detection[
                        "center_pixel"
                    ]["x"],

                "center_y":
                    detection[
                        "center_pixel"
                    ]["y"],

                "x1":
                    detection[
                        "bounding_box"
                    ]["x1"],

                "y1":
                    detection[
                        "bounding_box"
                    ]["y1"],

                "x2":
                    detection[
                        "bounding_box"
                    ]["x2"],

                "y2":
                    detection[
                        "bounding_box"
                    ]["y2"],

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


    csv_path = (
        OUTPUT_DIR /
        "anomaly_report.csv"
    )


    with open(
        csv_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        file.write(
            csv_data
        )


    # --------------------------------------------------------
    # DOWNLOAD REPORTS
    # --------------------------------------------------------

    st.header("📥 Download Reports")


    download_col1, download_col2 = (
        st.columns(2)
    )


    with download_col1:

        st.download_button(

            label="📄 Download JSON Report",

            data=json_data,

            file_name=
                "detection_report.json",

            mime=
                "application/json",

            use_container_width=True
        )


    with download_col2:

        st.download_button(

            label="📊 Download CSV Report",

            data=csv_data,

            file_name=
                "anomaly_report.csv",

            mime=
                "text/csv",

            use_container_width=True
        )


    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    if detections:

        st.success(
            f"✅ Analysis complete. "
            f"{len(detections)} potential anomaly(s) detected."
        )

    else:

        st.success(
            "✅ Analysis complete. "
            "No potential anomalies detected."
        )


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.divider()

st.caption(
    "MarineDebrisAI | AI-assisted side-scan sonar anomaly "
    "detection, confidence scoring and approximate geospatial localization"
)