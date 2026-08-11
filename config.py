import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Security ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # --- Database (SQLite, no external DB server needed) ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size

    # --- Model settings ---
    # Path to your trained Keras (.h5) model. Drop your model file here.
    MODEL_PATH = os.path.join(BASE_DIR, "model", "Brain_tumor_model.h5")

    # IMPORTANT: This must match the input size your model was TRAINED on.
    # Common sizes are (150, 150) or (224, 224). Change if needed.
    IMAGE_SIZE = (150, 150)

    # IMPORTANT: Order must exactly match the class-index order used while
    # training (e.g. the order returned by ImageDataGenerator.flow_from_directory,
    # which is alphabetical by default).
    CLASS_LABELS = ["Glioma", "Meningioma", "No Tumor", "Pituitary"]

    # Human-friendly descriptions shown on the result page / report
    CLASS_INFO = {
        "Glioma": "A tumor that arises from glial cells in the brain or spine. "
                  "Gliomas can vary widely in aggressiveness and location.",
        "Meningioma": "A tumor that forms in the meninges, the membranes that "
                      "surround the brain and spinal cord. Most are slow-growing "
                      "and non-cancerous.",
        "No Tumor": "No visible tumor pattern was detected in the scan by the model.",
        "Pituitary": "A tumor that develops in the pituitary gland, which can "
                     "affect hormone regulation throughout the body.",
    }
