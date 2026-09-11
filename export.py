from ultralytics import YOLO

def export_model():
    print("Loading PyTorch model...")
    model = YOLO("backend/best.pt")
    
    print("Exporting to ONNX format for faster CPU inference...")
    # Export the model
    path = model.export(format="onnx", imgsz=640, dynamic=False, simplify=True)
    
    print(f"Export successful! ONNX model saved at: {path}")
    print("\nNext steps:")
    print("1. Add 'onnxruntime' to your requirements.txt")
    print("2. Change api_server.py to load 'backend/best.onnx' instead of 'backend/best.pt'")

if __name__ == "__main__":
    export_model()
