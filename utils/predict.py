"""
Handles loading the trained .h5 model (once, at startup) and running
predictions on uploaded MRI images. No external API is used — everything
runs locally with TensorFlow/Keras.
"""

import os
import numpy as np
from PIL import Image

_model = None  # cached model instance (loaded lazily, only once)


def load_model():
    """Load the Keras model into memory. Called once when the app starts."""
    global _model
    if _model is None:
        from tensorflow.keras.models import load_model as keras_load_model
        from flask import current_app

        model_path = current_app.config["MODEL_PATH"]
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at '{model_path}'. "
                f"Place your trained .h5 file there (see README)."
            )
        _model = keras_load_model(model_path)
        print(f"[INFO] Brain tumor model loaded from: {model_path}")
    return _model


def preprocess_image(image_path, target_size):
    """Load an image from disk and prepare it exactly the way the model expects."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize(target_size)
    arr = np.array(img, dtype="float32") / 255.0  # normalize to 0-1
    arr = np.expand_dims(arr, axis=0)  # add batch dimension -> (1, H, W, 3)
    return arr


def predict_tumor(image_path, class_labels, image_size):
    """
    Run the model on a single image.

    Returns:
        predicted_label (str)
        confidence (float)   -> percentage 0-100 for the top class
        probabilities (dict) -> {label: percentage} for ALL classes
    """
    model = load_model()
    processed = preprocess_image(image_path, image_size)

    raw_predictions = model.predict(processed, verbose=0)[0]

    # If the model's last layer isn't already softmax, this keeps things
    # safe by normalizing outputs into probabilities that sum to 1.
    total = np.sum(raw_predictions)
    if total <= 0:
        raise ValueError("Model returned invalid prediction output.")
    normalized = raw_predictions / total

    probabilities = {
        label: round(float(normalized[i]) * 100, 2)
        for i, label in enumerate(class_labels)
    }

    best_index = int(np.argmax(normalized))
    predicted_label = class_labels[best_index]
    confidence = round(float(normalized[best_index]) * 100, 2)

    return predicted_label, confidence, probabilities
