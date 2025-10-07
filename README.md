# Fashion Backend API

A modern FastAPI backend for analyzing clothing images and generating AI-powered outfit recommendations. Supports Google Cloud Storage for image management, duplicate detection, and batch processing.

---

## 🚀 Features
- **Clothing Attribute Extraction**: Upload images and extract detailed clothing attributes
- **Outfit Recommendation**: Get AI-generated outfit suggestions based on your digital closet
- **Cloud Storage**: Images are stored in Google Cloud Storage (GCS) for scalability
- **Duplicate Detection**: Prevents reprocessing of the same image
- **Batch Processing**: Analyze multiple images in a single request
- **Comprehensive Logging**: User-specific, meaningful checkpoints for easy debugging

---

## 🗂️ Project Structure
```
fashion-backend/
├── app/                  # Main application code
│   ├── api/              # API routes
│   ├── core/             # Config, logging, storage
│   ├── models/           # Pydantic response models
│   └── services/         # Business logic (attribute & styler)
├── main.py               # App entry point
├── requirements.txt      # Python dependencies
├── test_gcs_integration.py # GCS integration test script
├── tests/                # Unit, integration, and performance tests
└── README.md             # This file
```

---

## ⚙️ Setup

### 1. Clone & Environment
```bash
git clone <repo-url>
cd fashion-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```
USE_GCS=true
GCS_BUCKET_NAME="your-gcs-bucket"
GCS_SERVICE_ACCOUNT_KEY="/path/to/key.json"
# For AI recommendations:
GEMINI_API_KEY="your_gemini_api_key"
OPENAI_API_KEY="your_openai_api_key"
```

---

## 🏃 Running the Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **API Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

---

## 📸 Attribute Extraction API

### POST `/api/v1/attribute_clothes`
Upload one or more images for clothing attribute analysis.

**Request:**
- `multipart/form-data` with one or more `files` fields

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg" -F "files=@image2.png"
```

**Response Example:**
```json
{
  "success": true,
  "message": "2 of 2 images processed successfully",
  "processing_timestamp": "2025-09-30T18:01:53.123456",
  "results": [
    {
      "image_info": {"filename": "shirt.jpg", ...},
      "status": "attributes_extracted",
      "attributes": {"category": "T-Shirt", ...},
      "error": null
    }
  ]
}
```

---

## 👗 Styler API (Outfit Recommendation)

### POST `/api/v1/styler`
Get outfit recommendations based on your uploaded clothing images.

**Request:**
- `application/x-www-form-urlencoded` or query params
- Required: `user_id`
- Optional: `city`, `weather`, `occasion`

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -H "accept: application/json" \
  -d "user_id=john_doe&city=Toronto&weather=fall&occasion=casual"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Outfit recommendation generated successfully for user 'john_doe'",
  "user_id": "john_doe",
  "styling_timestamp": "2025-09-30T18:45:22.123456",
  "request_parameters": {"city": "Toronto", ...},
  "outfit_recommendation": {
    "top": "navy_blazer_formal.jpg",
    "bottom": "charcoal_trousers_slim.jpg",
    "outerwear": "wool_coat_navy.jpg",
    ...
  },
  "outfit_images": {
    "top": "https://storage.googleapis.com/your-gcs-bucket/user_id/processed/navy_blazer_formal.jpg",
    "bottom": "https://storage.googleapis.com/your-gcs-bucket/user_id/processed/charcoal_trousers_slim.jpg",
    "outerwear": "https://storage.googleapis.com/your-gcs-bucket/user_id/processed/wool_coat_navy.jpg"
  },
  "available_items_count": 15,
  "error": null
}
```

---

## 🧪 Testing

### Run All Tests
```bash
python run_tests.py
```

### Run Unit/Integration/Performance Tests
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/performance/ -v
```

---

## 📝 Tips & Best Practices
- **Upload diverse clothing** for better outfit recommendations
- **Use clear user IDs** to keep your digital closet organized
- **Check logs** for user-specific processing and debugging
- **API keys**: Ensure your Gemini/OpenAI keys are set for AI-powered styling

---

## 💡 Next Steps
- Add more images to your closet for richer recommendations
- Experiment with different weather/occasion parameters
- Integrate with a frontend for a complete fashion assistant experience

---

## 📬 Support
For issues or feature requests, please open a GitHub issue.
