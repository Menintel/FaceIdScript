import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Set
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "FaceID API"
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/faceid.db"
    
    # Face recognition settings
    FACE_DETECTION_MODEL: str = "opencv"
    FACE_RECOGNITION_MODEL: str = "Facenet"
    DISTANCE_METRIC: str = "cosine"
    THRESHOLD: float = 0.6
    
    # Storage settings
    UPLOAD_FOLDER: str = str(BASE_DIR / "captured_faces")
    ALLOWED_EXTENSIONS: Set[str] = Field(default={'png', 'jpg', 'jpeg'})
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

# Create instance
settings = Settings()

# Create upload folder if it doesn't exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
