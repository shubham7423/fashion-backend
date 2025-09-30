from app.services.attribution.attributor import Attributor
from app.core.config import settings
from google import generativeai as genai
from PIL import Image
import json
import time
import random


class GeminiAttributor(Attributor):
    def __init__(self):
        super().__init__()
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def extract(self, image: Image.Image, image_filename: str = None) -> dict:
        # Get the prompt without the image placeholder
        prompt = self.get_prompt_text()

        # Retry logic for rate limiting
        max_retries = 3
        base_delay = 2  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                # Add a small delay before each request to respect rate limits
                if attempt > 0:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limit hit, waiting {delay:.1f} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                else:
                    # Small delay even on first attempt to be respectful
                    time.sleep(1)

                # Generate content with both text and image
                response = self.model.generate_content([prompt, image])

                # Extract the JSON from the response
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

            except Exception as e:
                error_message = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_message or "quota" in error_message.lower() or "rate" in error_message.lower():
                    if attempt < max_retries - 1:
                        # Will retry on next iteration
                        continue
                    else:
                        # Final attempt failed
                        return {
                            "error": f"Rate limit exceeded after {max_retries} attempts. Please wait a few minutes before trying again. Consider processing fewer images at once.",
                            "suggestion": "Try processing images one by one or in smaller batches to stay within rate limits."
                        }
                else:
                    # Non-rate-limit error, return immediately
                    return {"error": f"Failed to process image: {error_message}"}
        
        # This shouldn't be reached, but just in case
        return {"error": "Unexpected error in retry loop"}
