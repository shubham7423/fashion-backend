from app.services.attribution.attributor import Attributor
from app.core.config import settings
from app.core.retry_utils import RetryHandler, RetryConfig, create_rate_limit_error
from google import generativeai as genai
from PIL import Image
import json


class GeminiAttributor(Attributor):
    def __init__(self):
        super().__init__()
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def extract(self, image: Image.Image, image_filename: str = None) -> dict:
        """Extract clothing attributes from image using Gemini with retry logic."""
        # Get the prompt without the image placeholder
        prompt = self.get_prompt_text()
        
        # Configure retry behavior for Gemini API
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            initial_delay=1.0
        )
        retry_handler = RetryHandler(retry_config)
        
        def gemini_operation():
            """Execute Gemini API call."""
            # Generate content with both text and image
            response = self.model.generate_content([prompt, image])
            response_text = response.text.strip()
            
            # Try to parse the JSON response
            try:
                result = json.loads(response_text)
                # Add the image filename to the result after LLM processing
                if image_filename:
                    result["image"] = image_filename
                return result
            except json.JSONDecodeError:
                # If the response isn't valid JSON, try to extract it
                # Sometimes the model adds extra text, so we'll look for JSON
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    # Add the image filename to the result after LLM processing
                    if image_filename:
                        result["image"] = image_filename
                    return result
                else:
                    return {
                        "error": "Could not parse JSON response",
                        "raw_response": response_text,
                    }
        
        def error_handler(error_message: str, attempts: int) -> dict:
            """Handle errors from Gemini API."""
            if retry_handler.is_rate_limit_error(error_message):
                return create_rate_limit_error(attempts)
            else:
                return {"error": f"Failed to process image: {error_message}"}
        
        try:
            return retry_handler.execute_with_retry(
                gemini_operation,
                error_handler,
                context="Gemini attribute extraction"
            )
        except Exception as e:
            # Fallback error handling
            return {"error": f"Unexpected error in Gemini extraction: {str(e)}"}
