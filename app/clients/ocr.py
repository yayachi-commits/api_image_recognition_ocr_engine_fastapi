"""OCR client wrapper - exact same pipeline as original script"""

from paddleocr import PPStructure
from pathlib import Path
import json
from threading import Lock
from typing import Dict, Any, List
from ..internal.config import Settings
from ..internal.logs import get_logger

logger = get_logger("ocr.client")
PPSTRUCTURE_SUPPORTED_LANGS = {"en", "ch"}


class OCRClient:
    """Wraps PPStructure with exact settings from original script"""

    @staticmethod
    def _resolve_ppstructure_lang(requested_lang: str) -> str:
        normalized_lang = requested_lang.lower()
        if normalized_lang in PPSTRUCTURE_SUPPORTED_LANGS:
            return normalized_lang

        logger.warning(
            "PPStructure in paddleocr==2.7.0.3 only supports layout models for %s. "
            "Falling back from '%s' to 'en'.",
            sorted(PPSTRUCTURE_SUPPORTED_LANGS),
            requested_lang,
        )
        return "en"

    def __init__(self, settings: Settings):
        """Initialize pipeline with exact settings from image_recognition_engine.py"""
        resolved_lang = self._resolve_ppstructure_lang(settings.ocr_language)
        logger.info(
            "Initializing PPStructure with device=%s, requested_lang=%s, resolved_lang=%s",
            settings.ocr_device,
            settings.ocr_language,
            resolved_lang,
        )

        self.settings = settings
        self._predict_lock = Lock()
        self.pipeline = PPStructure(
            device=settings.ocr_device,                          # "gpu"
            lang=resolved_lang,                                  # layout models support en/ch in this version
            use_doc_orientation_classify=settings.use_doc_orientation_classify,  # True
            use_doc_unwarping=settings.use_doc_unwarping,         # False
            use_textline_orientation=settings.use_textline_orientation,  # False
        )
        logger.info("PPStructure pipeline initialized successfully")

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image and return results matching original output"""
        logger.info(f"Processing image: {image_path}")
        # PPStructure initialization is expensive, so the pipeline is reused.
        # The lock keeps concurrent requests from corrupting shared native state.
        with self._predict_lock:
            results = self.pipeline.predict(image_path)
        logger.info(f"OCR completed: {len(results)} pages")
        return self._parse_results(results)

    def _parse_results(self, results: List) -> Dict[str, Any]:
        """Parse pipeline results matching original script logic"""
        pages = []

        for idx, res in enumerate(results):
            page_num = idx + 1
            page_prefix = f"image_{page_num}"

            # Extract text from parsing_res_list (exact from original)
            text_output = []
            for block in res.get("parsing_res_list", []):
                if hasattr(block, 'content') and block.content:
                    text_output.append(block.content)

            pages.append({
                "page_number": page_num,
                "text": "\n".join(text_output),
                "raw_result": res,
                "page_prefix": page_prefix
            })

        return {
            "pages": pages,
            "total_pages": len(results)
        }

    def save_results(self, parsed_results: Dict, image_name: str, output_dir: Path) -> Dict[str, Any]:
        """Save outputs matching original script logic"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_outputs_dir = output_dir / image_name
        image_outputs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving results to {image_outputs_dir}")

        for page_data in parsed_results["pages"]:
            page_prefix = page_data["page_prefix"]
            res = page_data["raw_result"]

            # 1. Save JSON (exact from original)
            json_path = image_outputs_dir / f"{page_prefix}.json"
            res.save_to_json(save_path=str(json_path))
            page_data["json_file"] = str(json_path.relative_to(output_dir.parent))

            # 2. Save visualizations (exact from original)
            temp_dir = image_outputs_dir / ".temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            res.save_to_img(save_path=str(temp_dir))

            generated_images = []
            if temp_dir.exists():
                for img_file in sorted(temp_dir.glob("*.jpg")) + sorted(temp_dir.glob("*.png")):
                    new_name = f"{img_file.stem}_{page_prefix}{img_file.suffix}"
                    new_path = image_outputs_dir / new_name
                    img_file.rename(new_path)
                    generated_images.append(str(new_path.relative_to(output_dir.parent)))
                temp_dir.rmdir()

            page_data["generated_images"] = generated_images

            # 3. Save text (exact from original)
            txt_path = image_outputs_dir / f"{page_prefix}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(page_data["text"])
            page_data["text_file"] = str(txt_path.relative_to(output_dir.parent))

            # 4. Update JSON with image references (exact from original)
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            json_data["generated_images"] = generated_images
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

            logger.info(f"✓ Saved outputs for {page_prefix}")
            if generated_images:
                logger.info(f"  Generated {len(generated_images)} images")

        return parsed_results
