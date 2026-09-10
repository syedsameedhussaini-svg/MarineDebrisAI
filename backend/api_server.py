"""
MarineDebrisAI - FastAPI Backend Server
Directly runs YOLO11 inference using best.pt and real preprocessing.
No mock/demo detections.
"""

import sys
import time
import io
import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
import numpy as np
import cv2
import torch
import gc

torch.set_num_threads(2)

# Project root
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Existing Python functions
from ultralytics import YOLO
from preprocess import preprocess_with_analysis, TARGET_WIDTH, TARGET_HEIGHT
from sonar_analysis import validate_detection
from geotag import footprint_pixel_to_gps, valid_coordinate

MODEL_PATH = BASE_DIR / "best.pt"
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Trained model not found at: {MODEL_PATH}")

print(f"Loading MarineDebrisAI YOLO model from {MODEL_PATH}...")
model = YOLO(str(MODEL_PATH))
print(f"Model loaded successfully. Classes: {model.names}")

app = FastAPI(
    title="MarineDebrisAI API",
    description="Real YOLO inference backend for side-scan sonar object detection",
    version="2.0.0"
)

# Enable CORS for Vite dev server (http://localhost:5173) and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
@app.get("/health")
async def health_check():
    """Health check endpoint confirming model status."""
    return {
        "status": "online",
        "model": MODEL_PATH.name,
        "classes": model.names,
        "device": str(model.device),
        "timestamp": time.time()
    }


@app.post("/api/analyze")
@app.post("/analyze")
async def analyze_sonar_image(
    image: UploadFile = File(...),
    latitude_min: Optional[float] = Form(None),
    latitude_max: Optional[float] = Form(None),
    longitude_min: Optional[float] = Form(None),
    longitude_max: Optional[float] = Form(None),
    conf: float = Form(0.25),
    iou: float = Form(0.45)
):
    """
    Real sonar image analysis:
    1. Read input image bytes
    2. Preprocess with preprocess_with_analysis()
    3. Run YOLO inference using best.pt
    4. Validate detections with sonar_analysis.py
    5. Geotag if geographic footprint coordinates were provided
    6. Return real bounding boxes, classes, confidence, anomaly scores, and annotated image
    """
    try:
        # Read image
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

        try:
            original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to decode image file: {e}")

        original_width, original_height = original_image.size

        # 1. Preprocess image
        start_time = time.perf_counter()
        processed_image, preprocessing_analysis = preprocess_with_analysis(original_image)

        # 2. YOLO inference
        infer_start = time.perf_counter()
        with torch.inference_mode():
            results = model.predict(
                source=processed_image,
                conf=float(conf),
                iou=float(iou),
                imgsz=640,
                save=False,
                verbose=False
            )
        inference_time = time.perf_counter() - infer_start

        result = results[0]

        # 3. Render real YOLO annotated plot
        annotated_bgr = result.plot()
        _, annot_buffer = cv2.imencode(".jpg", annotated_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(annot_buffer).decode("utf-8")

        # Encode original image for browser display
        original_b64 = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8")

        # 4. Coordinate transformation back to original image resolution
        scale = min(TARGET_WIDTH / original_width, TARGET_HEIGHT / original_height)
        resized_w = max(1, int(round(original_width * scale)))
        resized_h = max(1, int(round(original_height * scale)))
        pad_x = (TARGET_WIDTH - resized_w) // 2
        pad_y = (TARGET_HEIGHT - resized_h) // 2

        # Validate footprint if user supplied complete coordinates
        has_gps = (
            latitude_min is not None and latitude_max is not None and
            longitude_min is not None and longitude_max is not None and
            valid_coordinate(latitude_min, longitude_min) and
            valid_coordinate(latitude_max, longitude_max) and
            latitude_min < latitude_max and longitude_min < longitude_max
        )

        detections = []
        orig_np = np.array(original_image)

        if result.boxes is not None and len(result.boxes) > 0:
            for i in range(len(result.boxes)):
                cls_id = int(result.boxes.cls[i])
                confidence = float(result.boxes.conf[i])
                px1, py1, px2, py2 = result.boxes.xyxy[i].tolist()

                # Map box back to original image space
                ox1 = max(0.0, min(float(original_width), (px1 - pad_x) / scale))
                oy1 = max(0.0, min(float(original_height), (py1 - pad_y) / scale))
                ox2 = max(0.0, min(float(original_width), (px2 - pad_x) / scale))
                oy2 = max(0.0, min(float(original_height), (py2 - pad_y) / scale))
                cx = (ox1 + ox2) / 2.0
                cy = (oy1 + oy2) / 2.0

                w_px = round(ox2 - ox1, 1)
                h_px = round(oy2 - oy1, 1)

                # Real acoustic validation & anomaly score
                validation = validate_detection(orig_np, [ox1, oy1, ox2, oy2], confidence)

                # Real GPS calculation (or None if footprint not provided)
                if has_gps:
                    lat, lon = footprint_pixel_to_gps(
                        cx, cy, original_width, original_height,
                        latitude_min, latitude_max, longitude_min, longitude_max
                    )
                else:
                    lat, lon = None, None

                detections.append({
                    "id": f"DET-{i+1:02d}",
                    "classification": model.names[cls_id],
                    "confidence": round(confidence * 100.0, 1),
                    "confidence_level": "High" if confidence >= 0.8 else ("Moderate" if confidence >= 0.6 else "Low"),
                    "anomaly_score": validation.get("anomaly_score"),
                    "anomaly_assessment": validation.get("assessment"),
                    "bounding_box": {
                        "x1": round(ox1, 1),
                        "y1": round(oy1, 1),
                        "x2": round(ox2, 1),
                        "y2": round(oy2, 1)
                    },
                    "center_pixel": {"x": round(cx, 1), "y": round(cy, 1)},
                    "width_pixels": w_px,
                    "height_pixels": h_px,
                    "latitude": lat,
                    "longitude": lon,
                    "shadow_score": validation.get("shadow_score"),
                    "texture_score": validation.get("texture_score"),
                    "edge_score": validation.get("edge_score"),
                    "warnings": validation.get("warnings", [])
                })

        total_time = time.perf_counter() - start_time
        quality = preprocessing_analysis.get("original_quality", {})

        gc.collect()

        return {
            "success": True,
            "filename": image.filename,
            "image_url": original_b64,
            "annotated_image_url": annotated_b64,
            "image_dimensions": {"width": original_width, "height": original_height},
            "has_gps": has_gps,
            "footprint": {
                "latitude_min": latitude_min,
                "latitude_max": latitude_max,
                "longitude_min": longitude_min,
                "longitude_max": longitude_max
            } if has_gps else None,
            "quality": {
                "quality_score": quality.get("quality_score"),
                "contrast": quality.get("contrast"),
                "brightness": quality.get("brightness"),
                "sharpness": quality.get("sharpness"),
                "dropout_detected": preprocessing_analysis.get("dropout_analysis", {}).get("dropout_detected", False)
            },
            "detections": detections,
            "total_processing_seconds": round(total_time, 3),
            "inference_seconds": round(inference_time, 3)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
