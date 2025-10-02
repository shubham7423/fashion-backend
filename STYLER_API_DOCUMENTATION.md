# Styler API Documentation

## Overview
The Styler API generates outfit recommendations based on a user's stored clothing attributes. It analyzes the user's digital closet (images processed through the `/attribute_clothes` endpoint) and creates stylish outfit combinations suitable for specific weather, city, and occasion parameters.

The API supports both Gemini (Google) and OpenAI models for generating recommendations. The default model can be configured via the `DEFAULT_STYLER` environment variable (set to "gemini" or "openai").

## Endpoint: POST /api/v1/styler

### Description
Generate outfit recommendations based on user's stored clothing attributes.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | Unique identifier for the user |
| `city` | string | No | "Toronto" | City for the occasion |
| `weather` | string | No | "early fall weather - expect temperatures around 15-20°C, partly cloudy" | Weather conditions |
| `occasion` | string | No | "casual day out" | The occasion type |

### Example Requests

#### cURL Examples

**Basic request with user ID only:**
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=john_doe"
```

**Full request with all parameters:**
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=john_doe&city=New York&weather=cold winter day - expect temperatures around 2-8°C, light snow&occasion=business meeting"
```

**URL parameters format:**
```bash
curl -X POST "http://localhost:8000/api/v1/styler?user_id=john_doe&city=Paris&weather=mild spring weather&occasion=dinner date" \
  -H "accept: application/json"
```

#### Postman Setup

1. **Method**: POST
2. **URL**: `http://localhost:8000/api/v1/styler`
3. **Headers**: 
   - `Accept: application/json`
4. **Body**: 
   - Select `x-www-form-urlencoded`
   - Add parameters:
     ```
     user_id: john_doe
     city: London
     weather: rainy autumn day - expect temperatures around 10-15°C, heavy rain
     occasion: weekend brunch
     ```

### Response Format

#### Successful Response
```json
{
  "success": true,
  "message": "Outfit recommendation generated successfully for user 'john_doe'",
  "user_id": "john_doe",
  "styling_timestamp": "2025-09-30T18:45:22.123456",
  "request_parameters": {
    "city": "New York",
    "weather": "cold winter day - expect temperatures around 2-8°C, light snow",
    "occasion": "business meeting"
  },
  "outfit_recommendation": {
    "top": "navy_blazer_formal.jpg",
    "bottom": "charcoal_trousers_slim.jpg",
    "outerwear": "wool_coat_navy.jpg",
    "justification": "This outfit combines professional navy and charcoal tones perfect for a business setting, with the wool coat providing essential warmth for winter weather.",
    "style_notes": "The slim-fit trousers balance the structured blazer, creating a modern professional silhouette suitable for business environments.",
    "other_accessories": "Consider a leather briefcase, classic watch, and wool scarf for added warmth and professional polish.",
    "weather_consideration": "The wool coat provides essential insulation for cold temperatures, while the layered approach allows for indoor comfort when the coat is removed."
  },
  "available_items_count": 15,
  "error": null
}
```

#### Error Response - User Not Found
```json
{
  "success": false,
  "message": "No clothing data found for user 'unknown_user'. Please upload some images first using /attribute_clothes endpoint.",
  "user_id": "unknown_user",
  "styling_timestamp": "2025-09-30T18:45:22.123456",
  "request_parameters": {
    "city": "Toronto",
    "weather": "early fall weather - expect temperatures around 15-20°C, partly cloudy",
    "occasion": "casual day out"
  },
  "outfit_recommendation": null,
  "available_items_count": 0,
  "error": "No valid clothing items available for styling"
}
```

#### Error Response - No Valid Items
```json
{
  "success": false,
  "message": "No valid clothing items found for user 'user123'. Please upload some images with valid clothing items first.",
  "user_id": "user123",
  "styling_timestamp": "2025-09-30T18:45:22.123456",
  "request_parameters": {
    "city": "Toronto",
    "weather": "early fall weather - expect temperatures around 15-20°C, partly cloudy",
    "occasion": "casual day out"
  },
  "outfit_recommendation": null,
  "available_items_count": 0,
  "error": "No valid clothing items available for styling"
}
```

### Outfit Recommendation Object

The `outfit_recommendation` object contains:

| Field | Type | Description |
|-------|------|-------------|
| `top` | string | Filename of the selected top item |
| `bottom` | string | Filename of the selected bottom item |
| `outerwear` | string or null | Filename of the selected outerwear item (if applicable) |
| `justification` | string | Explanation of why this outfit works together |
| `style_notes` | string | Professional styling tips about the combination |
| `other_accessories` | string | Accessory recommendations to complete the look |
| `weather_consideration` | string | How this outfit addresses the specified weather |

### Prerequisites

1. **User must exist**: The user must have previously uploaded images using `/attribute_clothes`
2. **Valid clothing items**: The user's JSON file must contain clothing items with valid attributes
3. **API key configured**: Gemini API key must be set in environment variables

### Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success - outfit recommendation generated |
| 400 | Bad Request - invalid parameters |
| 404 | Not Found - user has no clothing data |
| 500 | Internal Server Error - processing failed |

### Usage Flow

1. **Upload clothing images** using `/attribute_clothes` endpoint
2. **Call styler endpoint** with desired parameters
3. **Receive outfit recommendation** with specific clothing items
4. **Use the image filenames** to display the recommended outfit

### Example Use Cases

#### Business Professional
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -d "user_id=jane&city=San Francisco&weather=mild office environment&occasion=important presentation"
```

#### Casual Weekend
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -d "user_id=mike&city=Austin&weather=hot summer day - expect temperatures around 30-35°C&occasion=weekend picnic"
```

#### Date Night
```bash
curl -X POST "http://localhost:8000/api/v1/styler" \
  -d "user_id=sarah&city=Miami&weather=warm evening - expect temperatures around 22-26°C&occasion=romantic dinner"
```

### Tips for Best Results

1. **Upload diverse clothing**: Include tops, bottoms, and outerwear for better recommendations
2. **Be specific with weather**: Detailed weather descriptions yield better outfit choices  
3. **Clear occasion descriptions**: Specific occasions help the AI select appropriate formality levels
4. **Multiple items per category**: Upload several items in each category for more variety

### Rate Limiting

The styler endpoint uses either the Gemini API or OpenAI API, both of which have rate limits:
- If you encounter rate limiting, the system will automatically retry with exponential backoff
- Consider spacing requests if making multiple styling requests in succession
