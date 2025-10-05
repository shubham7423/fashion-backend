from app.services.styler.styler import Styler
from app.core.config import settings
from google import generativeai as genai
import json


class GeminiStyler(Styler):

    def __init__(self):
        super().__init__()
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def style(
        self,
        clothing_attributes: list,
        city: str = "Toronto",
        weather: str = "early fall weather - expect temperatures around 15-20°C, partly cloudy",
        occasion: str = "casual day out",
    ) -> str:
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
        # Convert the clothing attributes to a formatted JSON string for the prompt
        clothes_json = json.dumps(clothing_attributes, indent=2)

        # Get the prompt with the clothing attributes and styling parameters
        prompt = self.get_prompt_text(clothes_json, city, weather, occasion)

        # Define the operation function for retry logic
        def generate_response():
            # Generate content using the Gemini model
            response = self.model.generate_content(prompt)

            # Extract the response text
            response_text = response.text.strip()
            return response_text

        # Use the common retry logic
        response_text = self._retry_with_backoff(generate_response)

        # If response_text is an error message (JSON string), return it directly
        if response_text.startswith('{"error":'):
            return response_text

        # Otherwise, parse and validate the JSON response
        return self._parse_json_response(response_text)
