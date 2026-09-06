from ultralytics import YOLO
import torch
import os

# Load YOLO model
model = YOLO("yolo11n.pt")

# Input image
image_path = "data/images/sonar_test.jpg"

# Run detection on NVIDIA GPU
results = model.predict(
    source=image_path,
    device=0,
    conf=0.25,
    save=True,
    project="outputs",
    name="sonar_test",
    verbose=True
)

# Basic result information
result = results[0]

print("\n==============================")
print("MARINE DEBRIS AI - TEST")
print("==============================")
print("PyTorch:", torch.__version__)
print("GPU:", torch.cuda.get_device_name(0))
print("Detections:", len(result.boxes))
print("Result saved in: outputs/sonar_test")
print("==============================")