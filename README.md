# Fashion Backend API

A FastAPI application for processing fashion images and analyzing clothing attributes.

## Project Structure

```
fashion-backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app factory
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   └── routes.py             # API endpoints
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   └── config.py             # Application settings
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   └── response.py           # Response models
│   └── services/                 # Business logic
│       ├── __init__.py
│       └── attribution_service.py      # Image processing service
├── venv/                         # Virtual environment
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── test_api.py                   # API tests
└── README.md                     # This file
```

## Setup

### 1. Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Server
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Main URL**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## API Endpoints

### POST /api/v1/attribute_clothes
Process uploaded image files for clothing attribute analysis. The image is automatically compressed and resized to optimal dimensions (512x512) while maintaining aspect ratio for efficient clothing recognition. Images are processed in memory and not stored permanently.

**Image Processing Features:**
- **Automatic compression**: Images are resized to 512x512 pixels (maintaining aspect ratio)
- **High-quality resampling**: Uses LANCZOS algorithm for optimal quality
- **Format optimization**: JPEG quality set to 85% for balanced size/quality
- **Orientation correction**: Automatically fixes image rotation based on EXIF data
- **Memory efficiency**: Processing done in-memory without file storage

**Parameters:**
- `file`: Image file (multipart/form-data)

**Supported formats:**
- JPG/JPEG
- PNG
- GIF
- BMP
- WebP

**Max file size:** 10MB (original file)

**Response:**
```json
{
  "success": true,
  "message": "Image processed, compressed, and ready for attribute analysis",
  "image_info": {
    "filename": "example.jpg",
    "content_type": "image/jpeg",
    "file_size_bytes": 245760,
    "file_size_mb": 0.23
  },
  "processing_timestamp": "2025-09-30T14:30:22.123456",
  "status": "processed_and_ready",
  "attributes": null
}
```

### GET /
Returns basic API information.

### GET /api/v1/health
Health check endpoint.

## Usage Examples

### Using cURL
```bash
# Process an image for attribute analysis
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/image.jpg"
```

### Using Python requests
```python
import requests

url = "http://localhost:8000/api/v1/attribute_clothes"
files = {"file": open("path/to/your/image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## Image Processing

- **Automatic compression and resizing**: Images are optimized to 512x512 pixels for efficient processing
- **Aspect ratio preservation**: Original proportions are maintained during resizing
- **High-quality processing**: Uses LANCZOS resampling for superior image quality
- **Memory-only processing**: Images are processed in memory without permanent storage
- **Format validation**: Each image is validated for type and size before processing
- **EXIF orientation handling**: Automatically corrects image rotation
- **Optimal for clothing recognition**: Resolution balanced for material and texture identification
- **Ready for ML integration**: Processed images are optimized for clothing attribute analysis models

## Configuration

The application can be configured through environment variables or by modifying `app/core/config.py`:

```python
# Image processing settings
TARGET_WIDTH: int = 512           # Target width for clothing recognition
TARGET_HEIGHT: int = 512          # Target height for clothing recognition  
JPEG_QUALITY: int = 85           # JPEG compression quality (1-100)
MAINTAIN_ASPECT_RATIO: bool = True # Keep original aspect ratio when resizing
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB max upload size
```

## Project Structure
```
fashion-backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app factory
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   └── routes.py             # API endpoints
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   └── config.py             # Application settings
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   └── response.py           # Response models
│   └── services/                 # Business logic
│       ├── __init__.py
│       └── attribution_service.py      # Image processing service
├── venv/                         # Virtual environment
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── test_api.py                   # API tests
└── README.md                     # This file
```

## Next Steps

The processed images can be enhanced with:
1. Adding ML models for clothing attribute detection
2. Implementing color and pattern recognition
3. Adding style classification capabilities
4. Creating batch processing workflows
5. Adding real-time image analysis features
