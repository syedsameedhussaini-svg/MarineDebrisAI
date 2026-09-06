from pathlib import Path
import random
import shutil

# Dataset location
BASE = Path("data/AquaScan-1K")

IMAGES = BASE / "images"
LABELS = BASE / "labels"

# Reproducible split
random.seed(42)

# Get images
image_files = [
    p for p in IMAGES.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
]

random.shuffle(image_files)

# 80 / 10 / 10 split
n = len(image_files)
train_end = int(n * 0.80)
val_end = int(n * 0.90)

splits = {
    "train": image_files[:train_end],
    "val": image_files[train_end:val_end],
    "test": image_files[val_end:],
}

for split, files in splits.items():
    image_out = IMAGES / split
    label_out = LABELS / split

    image_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)

    for image in files:
        label = LABELS / f"{image.stem}.txt"

        if not label.exists():
            print(f"WARNING: Missing label for {image.name}")
            continue

        shutil.copy2(image, image_out / image.name)
        shutil.copy2(label, label_out / label.name)

    print(f"{split}: {len(files)} images")

print("\nDataset split complete!")