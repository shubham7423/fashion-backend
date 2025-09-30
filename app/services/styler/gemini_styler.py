from app.services.styler.styler import Styler
from app.core.config import settings
from google import generativeai as genai
import json
import time
import random

class GeminiStyler(Styler):

    def __init__(self):
        super().__init__()
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    def style(self, clothing_attributes: list, city: str = "Toronto", weather: str = "early fall weather - expect temperatures around 15-20°C, partly cloudy", occasion: str = "casual day out") -> str:
        """
        Generate a styled outfit from the given clothing attributes using Gemini model.
        
        Args:
            clothing_attributes: List of clothing items with their attributes
            city: The city for the occasion (default: "Toronto")
            weather: Weather conditions (default: "early fall weather - expect temperatures around 15-20°C, partly cloudy")
            occasion: The occasion type (default: "casual day out")
            
        Returns:
            str: JSON string containing the styled outfit recommendation
        """
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

                # Convert the clothing attributes to a formatted JSON string for the prompt
                clothes_json = json.dumps(clothing_attributes, indent=2)
                
                # Get the prompt with the clothing attributes and styling parameters
                prompt = self.get_prompt_text(clothes_json, city, weather, occasion)
                
                # Generate content using the Gemini model
                response = self.model.generate_content(prompt)
                
                # Extract the response text
                response_text = response.text.strip()
                
                # Try to parse and validate the JSON response
                try:
                    # Attempt to parse the JSON to ensure it's valid
                    outfit_json = json.loads(response_text)
                    return response_text
                except json.JSONDecodeError:
                    # If the response isn't valid JSON, try to extract it
                    # Sometimes the model adds extra text, so we'll look for JSON
                    start_idx = response_text.find("{")
                    end_idx = response_text.rfind("}") + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = response_text[start_idx:end_idx]
                        # Validate the extracted JSON
                        outfit_json = json.loads(json_str)
                        return json_str
                    else:
                        return json.dumps({
                            "error": "Could not parse JSON response from model",
                            "raw_response": response_text
                        })
                        
            except Exception as e:
                error_message = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_message or "quota" in error_message.lower() or "rate" in error_message.lower():
                    if attempt < max_retries - 1:
                        # Will retry on next iteration
                        continue
                    else:
                        # Final attempt failed
                        return json.dumps({
                            "error": f"Rate limit exceeded after {max_retries} attempts. Please wait a few minutes before trying again.",
                            "suggestion": "The free tier has limited requests per minute. Try again in a few minutes."
                        })
                else:
                    # Non-rate-limit error, return immediately
                    return json.dumps({
                        "error": f"Failed to generate outfit: {error_message}"
                    })
        
        # This shouldn't be reached, but just in case
        return json.dumps({
            "error": "Unexpected error in retry loop"
        })