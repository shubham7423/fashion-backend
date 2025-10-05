# API Testing Guide

## Testing the Enhanced Fashion Backend API

### Features Added:
1. **JSON Storage**: Attributes are automatically saved to `image_attributes.json`
2. **Duplicate Detection**: Duplicate images are detected using SHA-256 hash
3. **Image Storage**: Only processed images are saved (originals discarded)
4. **Multiple Image Support**: Process multiple images in a single request

## cURL Examples

### 1. Single Image Processing
```bash
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@your_image.jpg"
```

### 2. Multiple Images Processing
```bash
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.webp"
```

### 3. Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

## Response Examples

### New Image (First Time)
```json
{
  "success": true,
  "message": "1 of 1 images processed successfully",
  "processing_timestamp": "2025-09-30T18:01:53.123456",
  "total_images": 1,
  "successful_analyses": 1,
  "failed_analyses": 0,
  "results": [
    {
      "image_info": {
        "filename": "shirt.jpg",
        "content_type": "image/jpeg",
        "file_size_bytes": 245760,
        "file_size_mb": 0.23
      },
      "status": "attributes_extracted",
      "attributes": {
        "identifier": "top",
        "category": "T-Shirt",
        "gender": "unisex",
        "primary_color": "Navy",
        "style": "Casual",
        "description": "A casual navy blue t-shirt with regular fit.",
        "saved_images": {
          "processed": "/path/to/saved_images/processed/20250930_180153_shirt_abc12345_processed.jpg"
        },
        "processing_info": {
          "original_size": [1200, 800],
          "processed_size": [512, 341],
          "size_reduction_ratio": 0.146
        },
        "image_hash": "abc123def456..."
      },
      "error": null
    }
  ]
}
```

### Duplicate Image
```json
{
  "success": true,
  "message": "1 of 1 images processed successfully",
  "processing_timestamp": "2025-09-30T18:02:15.123456",
  "total_images": 1,
  "successful_analyses": 1,
  "failed_analyses": 0,
  "results": [
    {
      "image_info": {
        "filename": "shirt_copy.jpg",
        "content_type": "image/jpeg",
        "file_size_bytes": 245760,
        "file_size_mb": 0.23
      },
      "status": "duplicate_found",
      "attributes": {
        "identifier": "top",
        "category": "T-Shirt",
        "gender": "unisex",
        "primary_color": "Navy",
        "style": "Casual",
        "description": "A casual navy blue t-shirt with regular fit.",
        "duplicate_info": {
          "original_filename": "shirt.jpg",
          "original_processed_timestamp": "2025-09-30T18:01:53.123456",
          "is_duplicate": true
        }
      },
      "error": null
    }
  ]
}
```

## File Structure After Processing

```
fashion-backend/
├── image_attributes.json          # JSON file with all image attributes
├── saved_images/
│   └── processed/                 # Only processed images are saved
│       ├── 20250930_180153_shirt_abc12345_processed.jpg
│       ├── 20250930_180205_jeans_def67890_processed.jpg
│       └── ...
└── ...
```

## JSON File Structure

```json
{
  "images": {
    "sha256_hash_1": {
      "filename": "original_filename.jpg",
      "content_type": "image/jpeg",
      "file_size_bytes": 245760,
      "file_size_mb": 0.23,
      "attributes": {
        "identifier": "top",
        "category": "T-Shirt",
        // ... other attributes
      },
      "processed_timestamp": "2025-09-30T18:01:53.123456",
      "image_hash": "sha256_hash_1",
      "saved_paths": {
        "processed": "/path/to/processed/image.jpg"
      }
    }
  },
  "metadata": {
    "total_images": 1,
    "last_updated": "2025-09-30T18:01:53.123456"
  }
}
```

## Key Benefits

1. **No Storage Waste**: Only compressed, processed images are saved
2. **Duplicate Prevention**: Same image won't be processed twice
3. **Persistent Storage**: All attributes are saved to JSON for future reference
4. **Batch Processing**: Handle multiple images efficiently
5. **Error Handling**: Partial failures don't stop the entire batch
