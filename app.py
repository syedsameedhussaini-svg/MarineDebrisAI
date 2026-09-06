import streamlit as st
from pathlib import Path
from PIL import Image
from ultralytics import YOLO
import json
import csv
import io

from geotag import footprint_pixel_to_gps


# ==================================================
# MarineDebrisAI
# AI-Powered Sonar Object Detection + Geotagging
# ==================================================


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "best.pt"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="MarineDebrisAI",
    page_icon="🌊",
    layout="wide"
)


# ==================================================
# HEADER
# ==================================================

st.title("🌊 MarineDebrisAI")
st.subheader("AI-Powered Sonar Object Detection & Geotagging")

st.write(
    "Upload a sonar image, provide its geographic footprint, "
    "and MarineDebrisAI will detect objects and estimate "
    "their geographic coordinates."
)


# ==================================================
# MODEL CHECK
# ==================================================

if not MODEL_PATH.exists():

    st.error(
        f"❌ Model not found:\n\n{MODEL_PATH}"
    )

    st.stop()


# ==================================================
# LOAD MODEL
# ==================================================

@st.cache_resource
def load_model():

    return YOLO(
        str(MODEL_PATH)
    )


model = load_model()


# ==================================================
# SONAR GEOGRAPHIC FOOTPRINT
# ==================================================

st.write("### 🗺️ Sonar Survey Geographic Footprint")

st.info(
    "Enter the geographic boundaries covered by the sonar image. "
    "The coordinates generated for detected objects are "
    "approximate and depend on the accuracy of this footprint."
)


# --------------------------------------------------
# Latitude
# --------------------------------------------------

lat_col1, lat_col2 = st.columns(2)


with lat_col1:

    latitude_min = st.number_input(
        "Minimum Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=0.0,
        step=0.000001,
        format="%.6f"
    )


with lat_col2:

    latitude_max = st.number_input(
        "Maximum Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=0.01,
        step=0.000001,
        format="%.6f"
    )


# --------------------------------------------------
# Longitude
# --------------------------------------------------

lon_col1, lon_col2 = st.columns(2)


with lon_col1:

    longitude_min = st.number_input(
        "Minimum Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=0.0,
        step=0.000001,
        format="%.6f"
    )


with lon_col2:

    longitude_max = st.number_input(
        "Maximum Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=0.01,
        step=0.000001,
        format="%.6f"
    )


# ==================================================
# FOOTPRINT VALIDATION
# ==================================================

if latitude_min >= latitude_max:

    st.error(
        "❌ Maximum latitude must be greater than "
        "minimum latitude."
    )

    st.stop()


if longitude_min >= longitude_max:

    st.error(
        "❌ Maximum longitude must be greater than "
        "minimum longitude."
    )

    st.stop()


# ==================================================
# DISPLAY FOOTPRINT
# ==================================================

st.caption(
    f"Image footprint: "
    f"{latitude_min:.6f}° to {latitude_max:.6f}° latitude, "
    f"{longitude_min:.6f}° to {longitude_max:.6f}° longitude."
)


# ==================================================
# IMAGE UPLOAD
# ==================================================

st.write("### 📷 Upload Sonar Image")

uploaded_file = st.file_uploader(
    "Choose a sonar image",
    type=[
        "jpg",
        "jpeg",
        "png",
        "bmp",
        "tif",
        "tiff"
    ]
)


# ==================================================
# MAIN PIPELINE
# ==================================================

if uploaded_file is not None:

    # --------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------

    original_image = Image.open(
        uploaded_file
    ).convert("RGB")

    image_width, image_height = original_image.size


    # --------------------------------------------------
    # ORIGINAL IMAGE
    # --------------------------------------------------

    st.write("### Uploaded Sonar Image")

    st.image(
        original_image,
        caption=uploaded_file.name,
        use_container_width=True
    )


    # ==================================================
    # YOLO DETECTION
    # ==================================================

    with st.spinner(
        "🔍 Running MarineDebrisAI detection..."
    ):

        results = model.predict(
            source=original_image,
            conf=0.25,
            save=False,
            verbose=False
        )


    result = results[0]


    # ==================================================
    # BUILD DETECTION REPORT
    # ==================================================

    detections = []


    if result.boxes is not None:

        for i in range(
            len(result.boxes)
        ):

            # ------------------------------------------
            # CLASS
            # ------------------------------------------

            class_id = int(
                result.boxes.cls[i]
            )

            class_name = model.names[
                class_id
            ]


            # ------------------------------------------
            # CONFIDENCE
            # ------------------------------------------

            confidence = float(
                result.boxes.conf[i]
            )


            # ------------------------------------------
            # BOUNDING BOX
            # ------------------------------------------

            x1, y1, x2, y2 = (
                result.boxes.xyxy[i].tolist()
            )


            # ------------------------------------------
            # OBJECT CENTER
            # ------------------------------------------

            center_x = (
                x1 + x2
            ) / 2.0

            center_y = (
                y1 + y2
            ) / 2.0


            # ------------------------------------------
            # PIXEL → GPS
            # ------------------------------------------

            object_latitude, object_longitude = (
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


            # ------------------------------------------
            # OBJECT SIZE
            # ------------------------------------------

            width_pixels = (
                x2 - x1
            )

            height_pixels = (
                y2 - y1
            )


            # ------------------------------------------
            # DETECTION RECORD
            # ------------------------------------------

            detection = {

                "image":
                    uploaded_file.name,

                "classification":
                    class_name,

                "confidence":
                    round(
                        confidence * 100,
                        2
                    ),

                "bounding_box": {

                    "x1":
                        round(x1, 2),

                    "y1":
                        round(y1, 2),

                    "x2":
                        round(x2, 2),

                    "y2":
                        round(y2, 2)
                },

                "center_pixel": {

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
                    object_latitude,

                "longitude":
                    object_longitude
            }


            detections.append(
                detection
            )


    # ==================================================
    # ANNOTATED IMAGE
    # ==================================================

    annotated = result.plot()


    # ==================================================
    # DETECTION RESULTS
    # ==================================================

    st.write(
        "### 🎯 Detection Results"
    )


    result_col1, result_col2 = (
        st.columns([2, 1])
    )


    # --------------------------------------------------
    # IMAGE
    # --------------------------------------------------

    with result_col1:

        st.image(
            annotated,
            caption="AI Detection",
            use_container_width=True
        )


    # --------------------------------------------------
    # INFORMATION
    # --------------------------------------------------

    with result_col2:

        st.metric(
            "Objects Detected",
            len(detections)
        )


        st.write(
            "#### 🗺️ Image Footprint"
        )

        st.write(
            f"Latitude: "
            f"**{latitude_min:.6f} → "
            f"{latitude_max:.6f}**"
        )

        st.write(
            f"Longitude: "
            f"**{longitude_min:.6f} → "
            f"{longitude_max:.6f}**"
        )


        if detections:

            st.write(
                "#### 🔎 Detected Objects"
            )


            for number, detection in enumerate(
                detections,
                1
            ):

                st.write(
                    f"**{number}. "
                    f"{detection['classification']}**"
                )


                st.write(
                    "Confidence: "
                    f"**{detection['confidence']}%**"
                )


                st.write(
                    "Size: **"
                    f"{detection['width_pixels']} × "
                    f"{detection['height_pixels']} px**"
                )


                st.write(
                    "Estimated Coordinates:"
                )


                st.write(
                    f"**Latitude:** "
                    f"{detection['latitude']:.7f}"
                )


                st.write(
                    f"**Longitude:** "
                    f"{detection['longitude']:.7f}"
                )


                st.divider()


        else:

            st.info(
                "No objects detected."
            )


    # ==================================================
    # JSON REPORT
    # ==================================================

    json_path = (
        OUTPUT_DIR /
        "detection_report.json"
    )


    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            detections,
            f,
            indent=4
        )


    # ==================================================
    # CSV REPORT
    # ==================================================

    csv_buffer = io.StringIO()


    fieldnames = [

        "image",

        "classification",

        "confidence_percent",

        "x1",

        "y1",

        "x2",

        "y2",

        "center_x",

        "center_y",

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

        writer.writerow({

            "image":
                detection["image"],

            "classification":
                detection["classification"],

            "confidence_percent":
                detection["confidence"],

            "x1":
                detection["bounding_box"]["x1"],

            "y1":
                detection["bounding_box"]["y1"],

            "x2":
                detection["bounding_box"]["x2"],

            "y2":
                detection["bounding_box"]["y2"],

            "center_x":
                detection["center_pixel"]["x"],

            "center_y":
                detection["center_pixel"]["y"],

            "width_pixels":
                detection["width_pixels"],

            "height_pixels":
                detection["height_pixels"],

            "latitude":
                detection["latitude"],

            "longitude":
                detection["longitude"]
        })


    csv_data = (
        csv_buffer.getvalue()
    )


    # ==================================================
    # SAVE CSV
    # ==================================================

    csv_path = (
        OUTPUT_DIR /
        "anomaly_report.csv"
    )


    with open(
        csv_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        f.write(
            csv_data
        )


    # ==================================================
    # REPORT DOWNLOADS
    # ==================================================

    st.write(
        "### 📄 Reports"
    )


    download_col1, download_col2 = (
        st.columns(2)
    )


    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    with download_col1:

        st.download_button(

            label="⬇️ Download JSON Report",

            data=json.dumps(
                detections,
                indent=4
            ),

            file_name=
                "detection_report.json",

            mime=
                "application/json"
        )


    # --------------------------------------------------
    # CSV
    # --------------------------------------------------

    with download_col2:

        st.download_button(

            label="⬇️ Download CSV Report",

            data=csv_data,

            file_name=
                "anomaly_report.csv",

            mime=
                "text/csv"
        )


    # ==================================================
    # SUCCESS
    # ==================================================

    st.success(
        "✅ Detection and approximate geotagging complete."
    )


    # ==================================================
    # OUTPUT INFORMATION
    # ==================================================

    with st.expander(
        "📁 Output Information"
    ):

        st.write(
            f"JSON report: `{json_path}`"
        )

        st.write(
            f"CSV report: `{csv_path}`"
        )