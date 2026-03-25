"""OCR API routes"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from functools import lru_cache
from pathlib import Path
import tempfile
from ..internal.config import Settings, get_settings
from ..internal.models import OCRResponse
from ..orchestrator.manager import OCRManager
from ..internal.logs import get_logger

logger = get_logger("router.ocr")

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


@lru_cache(maxsize=1)
def _get_cached_ocr_manager() -> OCRManager:
    """Keep a single OCR pipeline per process to avoid costly reinitialization."""
    return OCRManager(get_settings())


def get_ocr_manager(_: Settings = Depends(get_settings)) -> OCRManager:
    """Dependency: get OCR manager instance"""
    return _get_cached_ocr_manager()


@router.post("/process", response_model=OCRResponse)
async def process_image(
    file: UploadFile = File(...),
    manager: OCRManager = Depends(get_ocr_manager),
) -> OCRResponse:
    """
    Process an image file through OCR pipeline

    Args:
        file: Image file to process
        manager: OCR manager instance

    Returns:
        OCR processing results with extracted text and generated outputs
    """
    logger.info(f"Received file upload: {file.filename}")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in manager.settings.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {file_ext}. Supported formats: {manager.settings.supported_formats}",
        )

    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(
            suffix=file_ext, delete=False, dir=manager.settings.output_dir
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        logger.info(f"Saved upload to: {tmp_path}")

        # Process the image
        result = await manager.process_image(tmp_path)

        # Clean up temporary file (results are already saved by manager)
        Path(tmp_path).unlink(missing_ok=True)

        return OCRResponse(
            success=True,
            input_file=file.filename,
            pages=result["pages"],
            total_pages=result["total_pages"],
            output_dir=result["output_dir"],
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File error: {str(e)}")
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "OCR API"}
