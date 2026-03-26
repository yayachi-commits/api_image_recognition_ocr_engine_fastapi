"""OCR client wrapper - exact same pipeline as original script"""

from copy import deepcopy
import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from paddleocr import PPStructure, PaddleOCR, save_structure_res

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
            "PPStructure layout models only support %s in paddleocr==2.7.0.3. "
            "Falling back from '%s' to 'en'.",
            sorted(PPSTRUCTURE_SUPPORTED_LANGS),
            requested_lang,
        )
        return "en"

    @staticmethod
    def _extract_text_from_region(region: Dict[str, Any]) -> str:
        region_result = region.get("res")
        if isinstance(region_result, list):
            texts = []
            for item in region_result:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        texts.append(text)
            return "\n".join(texts)

        if isinstance(region_result, dict):
            html = region_result.get("html")
            if html:
                return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)

        return ""

    @staticmethod
    def _extract_text_pages_from_ocr_results(ocr_results: Any) -> List[str]:
        if not isinstance(ocr_results, list):
            return []

        pages = []
        for page in ocr_results:
            lines = []
            if isinstance(page, list):
                for item in page:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue

                    rec_result = item[1]
                    if isinstance(rec_result, (list, tuple)) and rec_result:
                        text = rec_result[0]
                        if text:
                            lines.append(str(text))

            pages.append("\n".join(lines))

        return pages

    @staticmethod
    def _make_json_serializable(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: OCRClient._make_json_serializable(item)
                for key, item in value.items()
                if key != "img"
            }
        if isinstance(value, list):
            return [OCRClient._make_json_serializable(item) for item in value]
        if isinstance(value, tuple):
            return [OCRClient._make_json_serializable(item) for item in value]
        if hasattr(value, "tolist"):
            try:
                return OCRClient._make_json_serializable(value.tolist())
            except TypeError:
                pass
        if hasattr(value, "item"):
            try:
                return value.item()
            except (TypeError, ValueError):
                pass
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

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
        self.requested_lang = settings.ocr_language.lower()
        self.structure_lang = resolved_lang
        self._structure_lock = Lock()
        self._text_lock = Lock()
        self.pipeline = PPStructure(
            device=settings.ocr_device,                          # "gpu"
            lang=resolved_lang,                                  # layout models only support en/ch here
            use_doc_orientation_classify=settings.use_doc_orientation_classify,  # True
            use_doc_unwarping=settings.use_doc_unwarping,         # False
            use_textline_orientation=settings.use_textline_orientation,  # False
        )
        logger.info("PPStructure pipeline initialized successfully")

        self.text_pipeline = None
        if self.requested_lang != self.structure_lang:
            logger.info(
                "Initializing PaddleOCR text pipeline with requested_lang=%s for OCR text extraction",
                self.requested_lang,
            )
            self.text_pipeline = PaddleOCR(
                use_angle_cls=False,
                lang="fr",
                use_gpu=settings.ocr_device.lower() == "gpu",
                show_log=False,
            )
            logger.info("PaddleOCR text pipeline initialized successfully")

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image and return results matching original output"""
        logger.info(f"Processing image: {image_path}")
        with self._structure_lock:
            results = self.pipeline(image_path)

        text_results = None
        if self.text_pipeline is not None:
            with self._text_lock:
                text_results = self.text_pipeline.ocr(image_path, cls=False)

        if isinstance(results, dict):
            results = [results]

        logger.info(f"OCR completed: {len(results)} pages")
        return self._parse_results(results, text_results=text_results)

    def _parse_results(self, results: List, text_results: Any = None) -> Dict[str, Any]:
        """Parse pipeline results matching original script logic"""
        pages = []
        text_pages = self._extract_text_pages_from_ocr_results(text_results)

        if not results:
            total_pages = max(1, len(text_pages))
            if not text_pages:
                text_pages = [""]

            return {
                "pages": [
                    {
                        "page_number": page_number,
                        "text": text_pages[page_number - 1] if page_number - 1 < len(text_pages) else "",
                        "raw_results": [],
                        "page_prefix": f"image_{page_number}",
                    }
                    for page_number in range(1, total_pages + 1)
                ],
                "total_pages": total_pages,
            }

        pages_by_index: Dict[int, List[Dict[str, Any]]] = {}
        for region in results:
            page_index = int(region.get("img_idx", 0))
            pages_by_index.setdefault(page_index, []).append(region)

        for page_offset, page_index in enumerate(sorted(pages_by_index), start=1):
            page_regions = pages_by_index[page_index]
            text_output = []
            for region in page_regions:
                text = self._extract_text_from_region(region)
                if text:
                    text_output.append(text)

            page_text = "\n".join(text_output)
            if page_offset - 1 < len(text_pages) and text_pages[page_offset - 1]:
                page_text = text_pages[page_offset - 1]

            pages.append({
                "page_number": page_offset,
                "text": page_text,
                "raw_results": page_regions,
                "page_prefix": f"image_{page_offset}",
            })

        return {
            "pages": pages,
            "total_pages": len(pages)
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
            page_results = page_data["raw_results"]

            page_structure_dir = image_outputs_dir / page_prefix
            generated_images = []

            try:
                save_structure_res(
                    deepcopy(page_results),
                    str(image_outputs_dir),
                    page_prefix,
                    img_idx=page_data["page_number"] - 1,
                )
                for img_file in sorted(page_structure_dir.rglob("*.jpg")) + sorted(page_structure_dir.rglob("*.png")):
                    generated_images.append(str(img_file.relative_to(output_dir.parent)))
            except Exception as exc:
                logger.warning("Could not save structure artifacts for %s: %s", page_prefix, exc)

            # 1. Save JSON
            json_path = image_outputs_dir / f"{page_prefix}.json"
            json_payload = {
                "page_number": page_data["page_number"],
                "text": page_data["text"],
                "regions": self._make_json_serializable(page_results),
                "generated_images": generated_images,
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_payload, f, indent=4, ensure_ascii=False)
            page_data["json_file"] = str(json_path.relative_to(output_dir.parent))

            # 2. Save text
            txt_path = image_outputs_dir / f"{page_prefix}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(page_data["text"])
            page_data["text_file"] = str(txt_path.relative_to(output_dir.parent))
            page_data["generated_images"] = generated_images

            logger.info(f"✓ Saved outputs for {page_prefix}")
            if generated_images:
                logger.info(f"  Generated {len(generated_images)} images")

        return parsed_results
