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
- `OCR_LANGUAGE`: Language code used by `PPStructure` (default: "en")
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
pip install .
```

### Run locally
```bash
uvicorn app.main:app --reload
```

### Docker
```bash
docker build -t ocr-engine:latest .
mkdir -p outputs
docker run --rm \
  -p 8000:8000 \
  -e OCR_DEVICE=cpu \
  -e OCR_LANGUAGE=en \
  -v "$(pwd)/outputs:/app/outputs" \
  ocr-engine:latest
```

To preload PaddleOCR models during the image build and keep the runtime filesystem read-only, keep the default build arg:

```bash
docker build \
  --build-arg OCR_LANGUAGE=en \
  --build-arg PRELOAD_PADDLE_MODELS=true \
  -t ocr-engine:latest .
```

With `paddleocr==2.7.0.3`, `PPStructure` layout models support `en` and `ch`. If another language is requested, the app falls back to `en` to avoid startup failures.

## Output Structure

For each processed image, the following files are generated:
- `{image_name}_{page_number}.json` - Structured OCR result data
- `{image_name}_{page_number}.txt` - Extracted text
- `{image_name}_{page_number}_*.jpg` - Visualization images (tables, text regions)
