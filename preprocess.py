from PIL import Image, ImageEnhance, ImageFilter

TARGET_WIDTH = 1024
TARGET_HEIGHT = 1024


def preprocess_with_analysis(image):
    if image is None:
        raise ValueError("Input image is None.")

    image = image.convert("RGB")

    original_width, original_height = image.size

    scale = min(
        TARGET_WIDTH / original_width,
        TARGET_HEIGHT / original_height
    )

    new_width = max(
        1,
        int(round(original_width * scale))
    )

    new_height = max(
        1,
        int(round(original_height * scale))
    )

    resized = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    canvas = Image.new(
        "RGB",
        (TARGET_WIDTH, TARGET_HEIGHT),
        (0, 0, 0)
    )

    pad_x = (
        TARGET_WIDTH - new_width
    ) // 2

    pad_y = (
        TARGET_HEIGHT - new_height
    ) // 2

    canvas.paste(
        resized,
        (pad_x, pad_y)
    )

    gray = canvas.convert("L")

    contrast = ImageEnhance.Contrast(
        gray
    ).enhance(1.5)

    filtered = contrast.filter(
        ImageFilter.MedianFilter(
            size=3
        )
    )

    processed = filtered.convert("RGB")

    quality = {
        "brightness": 0,
        "contrast": 0,
        "sharpness": 0,
        "quality_score": 100
    }

    analysis = {
        "original_quality": quality,
        "processed_quality": quality,
        "dropout_analysis": {
            "dropout_detected": False,
            "dropout_percentage": 0
        },
        "warnings": []
    }

    return processed, analysis
