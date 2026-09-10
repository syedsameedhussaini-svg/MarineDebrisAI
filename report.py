import json
import csv
from pathlib import Path

INPUT = Path(r"C:\MarineDebrisAI-Web\output\detection_report.json")
OUTPUT = Path(r"C:\MarineDebrisAI-Web\output\anomaly_report.csv")
with open(INPUT, "r", encoding="utf-8") as f:
    detections = json.load(f)

rows = []

for d in detections:
    rows.append({
        "image": d["image"],
        "classification": d["classification"],
        "confidence_percent": d["confidence"],
        "x1": d["bounding_box"]["x1"],
        "y1": d["bounding_box"]["y1"],
        "x2": d["bounding_box"]["x2"],
        "y2": d["bounding_box"]["y2"],
        "width_pixels": d["width_pixels"],
        "height_pixels": d["height_pixels"],
        "latitude": "",
        "longitude": ""
    })

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("===================================")
print(" ANOMALY REPORT CREATED")
print("===================================")
print(f"Detections: {len(rows)}")
print(f"CSV saved: {OUTPUT}")
print("===================================")