# Image Recognition OCR Engine API

A FastAPI-based OCR processing service powered by PaddleOCR for document analysis and text extraction.

## Features

- 🎯 PaddleOCR-powered document processing
- 📄 Multi-format support (PNG, JPG, JPEG, TIFF, BMP, WebP, PDF)
- 🔧 RESTful API with FastAPI
- 📊 Structured JSON output with document analysis
- 🖼️ Automatic visualization image generation
- ⚡ Async request handling

## Project Structure

```
app/
├── clients/          # OCR client wrapper
├── internal/         # Config, models, logging
├── orchestrator/     # Processing workflow coordinator
├── routers/          # API endpoints
├── app.py           # FastAPI application factory
└── main.py          # ASGI entry point
```

## Configuration

Settings are managed via environment variables (see `.env.example`):

- `OCR_DEVICE`: "gpu" or "cpu"
- `OCR_LANGUAGE`: Language code (default: "fr")
- `USE_DOC_ORIENTATION_CLASSIFY`: Enable document orientation detection
- `USE_DOC_UNWARPING`: Enable document unwarping
- `USE_TEXTLINE_ORIENTATION`: Enable textline orientation detection
- `PORT`: API port (default: 8000)
- `OUTPUT_DIR`: Output directory for results (default: outputs)

## API Endpoints

### POST /api/v1/ocr/process
Process an image file through the OCR pipeline.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/process" \
  -F "file=@image.png"
```

**Response:**
```json
{
  "success": true,
  "input_file": "image.png",
  "total_pages": 1,
  "output_dir": "outputs/image",
  "pages": [
    {
      "page_number": 1,
      "text": "Extracted text content...",
      "json_file": "outputs/image/image_1.json",
      "text_file": "outputs/image/image_1.txt",
      "generated_images": ["outputs/image/image_1_table.jpg"]
    }
  ]
}
```

### GET /health
Health check endpoint.

## Development

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run locally
```bash
uvicorn app.main:app --reload
```

### Docker
```bash
docker build -t ocr-engine .
docker run -p 8000:8000 -v $(pwd)/outputs:/app/outputs ocr-engine
```

## Output Structure

For each processed image, the following files are generated:
- `{image_name}_{page_number}.json` - Structured OCR result data
- `{image_name}_{page_number}.txt` - Extracted text
- `{image_name}_{page_number}_*.jpg` - Visualization images (tables, text regions)
