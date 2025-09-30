# Image Processing Examples

This document provides examples of how to test the image processing functionality.

## API Endpoints

### Image Processing
**Endpoint**: `POST /api/v1/attribute_clothes`  
**Description**: Process one or more images in a single request  
**Max files**: 10 images per request  

## Testing with cURL

### Single Image
```bash
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg"
```

### Multiple Images
```bash
curl -X POST "http://localhost:8000/api/v1/attribute_clothes" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.webp"
```

## Testing with Postman

### For Image Processing:

1. **Method**: POST
2. **URL**: `http://localhost:8000/api/v1/attribute_clothes`
3. **Headers**: 
   - `Accept: application/json`
4. **Body**: 
   - Select `form-data`
   - Add one or more entries with key `files` (not `files[]`)
   - For each entry, set type to `File` and choose your image file
   - Example:
     ```
     Key: files | Type: File | Value: image1.jpg
     Key: files | Type: File | Value: image2.png  
     Key: files | Type: File | Value: image3.webp
     ```

## Response Format

### Image Processing Response
```json
{
  "success": true,
  "message": "2 of 3 images processed successfully", 
  "processing_timestamp": "2025-09-30T10:30:22.123456",
  "total_images": 3,
  "successful_analyses": 2,
  "failed_analyses": 1,
  "results": [
    {
      "image_info": {
        "filename": "image1.jpg",
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
        "occasion": "Everyday",
        "weather": "Warm",
        "fit": "Regular Fit",
        "sleeve_length": "Short Sleeve",
        "description": "A casual navy blue t-shirt with regular fit."
      },
      "error": null
    },
    {
      "image_info": {
        "filename": "image2.png",
        "content_type": "image/png", 
        "file_size_bytes": 512000,
        "file_size_mb": 0.5
      },
      "status": "attributes_extracted",
      "attributes": {
        "identifier": "bottom",
        "category": "Jeans",
        "gender": "unisex", 
        "primary_color": "Indigo",
        "style": "Casual",
        "occasion": "Everyday",
        "weather": "Mild",
        "fit": "Slim Fit",
        "sleeve_length": null,
        "description": "Classic indigo slim-fit jeans."
      },
      "error": null
    },
    {
      "image_info": {
        "filename": "image3.webp",
        "content_type": "image/webp",
        "file_size_bytes": 102400,
        "file_size_mb": 0.1
      },
      "status": "error", 
      "attributes": null,
      "error": "Invalid image format: cannot identify image file"
    }
  ]
}
```

## Supported Image Formats

- JPEG/JPG
- PNG
- GIF
- BMP  
- WebP
- AVIF

## Limitations

- **Max file size**: 10MB per image
- **Max files per request**: 10 images
- **Processing**: Images are processed in memory and not stored
- **Compression**: All images are automatically resized to 512x512 (maintaining aspect ratio)

## Error Handling

The API handles errors gracefully:
- Invalid file formats are rejected
- Oversized files are rejected  
- Processing errors for individual images don't stop the entire batch
- Each image result includes error information if processing failed
- Partial success is supported (some images succeed, others fail)
