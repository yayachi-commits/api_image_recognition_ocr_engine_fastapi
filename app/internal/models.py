"""Pydantic models for requests/responses"""

from pydantic import BaseModel
from typing import Optional, List


class OCRPageResult(BaseModel):
    """Result for each page (matching original output)"""
    page_number: int
    text: str
    json_file: Optional[str] = None
    text_file: Optional[str] = None
    generated_images: List[str] = []


class OCRResponse(BaseModel):
    """API response matching original output format"""
    success: bool = True
    input_file: str
    pages: List[OCRPageResult]
    total_pages: int
    output_dir: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[str] = None
