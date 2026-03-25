"""OCR processing orchestrator - coordinates the OCR workflow"""

from pathlib import Path
from typing import Dict, Any, Optional
import uuid
from fastapi.concurrency import run_in_threadpool
from ..clients.ocr import OCRClient
from ..internal.config import Settings
from ..internal.logs import get_logger

logger = get_logger("orchestrator.manager")


class OCRManager:
    """Orchestrates OCR processing workflow"""

    def __init__(self, settings: Settings):
        """Initialize orchestrator with OCR client"""
        self.settings = settings
        self.ocr_client = OCRClient(settings)
        logger.info("OCRManager initialized")

    async def process_image(self, image_path: str, output_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single image through the OCR pipeline

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing OCR results
        """
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Processing image: {image_path}")

        # Validate image exists
        path = Path(image_path)
        if not path.exists():
            logger.error(f"[{request_id}] Image not found: {image_path}")
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Validate format
        if path.suffix.lower() not in self.settings.supported_formats:
            logger.error(f"[{request_id}] Unsupported format: {path.suffix}")
            raise ValueError(f"Unsupported format: {path.suffix}. Supported: {self.settings.supported_formats}")

        try:
            # Process the image
            logger.info(f"[{request_id}] Running OCR pipeline...")
            parsed_results = await run_in_threadpool(self.ocr_client.process_image, image_path)

            # Save results to output directory
            output_dir = Path(self.settings.output_dir)
            image_name = output_name or path.stem
            logger.info(f"[{request_id}] Saving results to {output_dir}")
            final_results = await run_in_threadpool(
                self.ocr_client.save_results,
                parsed_results,
                image_name,
                output_dir,
            )

            logger.info(f"[{request_id}] ✓ Processing completed successfully")
            return {
                "success": True,
                "request_id": request_id,
                "input_file": str(path),
                "pages": final_results["pages"],
                "total_pages": final_results["total_pages"],
                "output_dir": str(output_dir / image_name),
            }

        except Exception as e:
            logger.error(f"[{request_id}] Error processing image: {str(e)}", exc_info=True)
            raise
