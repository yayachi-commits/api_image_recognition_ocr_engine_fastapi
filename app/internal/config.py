"""Configuration matching original image_recognition_engine.py"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Settings from original script"""

    # API
    app_name: str = Field(default="Image Recognition OCR Engine", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    port: int = Field(default=8000, validation_alias="PORT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")

    # OCR Pipeline (EXACT from original)
    ocr_device: str = Field(default="gpu", validation_alias="OCR_DEVICE")
    ocr_language: str = Field(default="fr", validation_alias="OCR_LANGUAGE")
    use_doc_orientation_classify: bool = Field(default=True, validation_alias="USE_DOC_ORIENTATION_CLASSIFY")
    use_doc_unwarping: bool = Field(default=False, validation_alias="USE_DOC_UNWARPING")
    use_textline_orientation: bool = Field(default=False, validation_alias="USE_TEXTLINE_ORIENTATION")

    # Output
    output_dir: str = Field(default="outputs", validation_alias="OUTPUT_DIR")

    # Formats
    supported_formats: set = Field(
        default={".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".pdf"},
        exclude=True
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
