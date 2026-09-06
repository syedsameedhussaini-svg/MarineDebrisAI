from ultralytics import YOLO
from pathlib import Path
import json
import sys

# --------------------------------------------------
# MarineDebrisAI - Detection Pipeline
# --------------------------------------------------

MODEL_PATH = r".\best.pt"
OUTPUT_DIR = Path(r"C:\MarineDebrisAI-Web\output")

# Check model
if not Path(MODEL_PATH).exists():
    print("ERROR: best.pt not found.")
    sys.exit(1)

# Check input
if len(sys.argv) < 2:
    print("Usage:")
    print(r'python predict.py "path\to\sonar_image.jpg"')
    sys.exit(1)

IMAGE_PATH = Path(sys.argv[1])

if not IMAGE_PATH.exists():
    print(f"ERROR: Image not found: {IMAGE_PATH}")
    sys.exit(1)

# Create output folder
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\nLoading MarineDebrisAI model...")
model = YOLO(MODEL_PATH)

print(f"Analyzing: {IMAGE_PATH.name}")

# Run detection
results = model.predict(
    source=str(IMAGE_PATH),
    conf=0.25,
    save=True,
    project=str(OUTPUT_DIR),
    name="detections",
    exist_ok=True
)

# Build structured report
report = []

for result in results:
    if result.boxes is None:
        continue

    boxes = result.boxes

    for i in range(len(boxes)):
        class_id = int(boxes.cls[i])
        confidence = float(boxes.conf[i])

        x1, y1, x2, y2 = boxes.xyxy[i].tolist()

        class_name = model.names[class_id]

        report.append({
            "image": IMAGE_PATH.name,
            "classification": class_name,
            "confidence": round(confidence * 100, 2),
            "bounding_box": {
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2)
            },
            "width_pixels": round(x2 - x1, 2),
            "height_pixels": round(y2 - y1, 2)
        })

# Save JSON report
json_path = OUTPUT_DIR / "detection_report.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=4)

print("\n===================================")
print(" DETECTION COMPLETE")
print("===================================")
print(f"Objects detected: {len(report)}")
print(f"Report saved: {json_path}")
print(f"Images saved: {OUTPUT_DIR / 'detections'}")
print("===================================\n")