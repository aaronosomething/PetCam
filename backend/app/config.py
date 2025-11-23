import os
from pathlib import Path

basedir = Path(__file__).resolve().parent.parent

class Config:
    # Flask
    SECRET_KEY = os.environ.get("PETCAM_SECRET_KEY", "change-me-in-prod")

    # Database
    DATABASE_PATH = os.environ.get("PETCAM_DB_PATH", str(basedir / "data" / "petcam.db"))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Storage paths
    IMAGES_DIR = Path(os.environ.get("PETCAM_IMAGES_DIR", str(basedir / "data" / "images")))
    THUMBS_DIR = Path(os.environ.get("PETCAM_THUMBS_DIR", str(basedir / "data" / "thumbnails")))

    # Capture settings
    CAPTURE_INTERVAL_SECONDS = int(os.environ.get("PETCAM_INTERVAL", "300"))
    IMAGE_RESOLUTION = os.environ.get("PETCAM_RESOLUTION", "1280x720")
    JPEG_QUALITY = int(os.environ.get("PETCAM_JPEG_QUALITY", "85"))

    # Retention
    RETENTION_DAYS = int(os.environ.get("PETCAM_RETENTION_DAYS", "7"))
    MAX_STORAGE_BYTES = int(os.environ.get("PETCAM_MAX_STORAGE_BYTES", "10737418240"))  # 10 GB

    # fswebcam command template
    FSWEBCAM_CMD = os.environ.get(
        "PETCAM_FSWEBCAM_CMD",
        "fswebcam -r {resolution} --no-banner -S 2 {outfile}"
    )

    @classmethod
    def ensure_dirs(cls):
        cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        cls.THUMBS_DIR.mkdir(parents=True, exist_ok=True)
        data_dir = Path(cls.DATABASE_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)
