from app.services.styler.styler import Styler
from app.core.config import settings
from openai import OpenAI
import json


class OpenAIStyler(Styler):

    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Using GPT-4o-mini for cost efficiency

    def style(
        self,
        clothing_attributes: list,
        city: str = "Toronto",
        weather: str = "early fall weather - expect temperatures around 15-20°C, partly cloudy",
        occasion: str = "casual day out",
    ) -> str:
        """
        Generate a styled outfit from the given clothing attributes using OpenAI model.

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
            # Generate content using the OpenAI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI fashion stylist. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            return response_text

        # Use the common retry logic
        response_text = self._retry_with_backoff(generate_response)

        # If response_text is an error message (JSON string), return it directly
        if response_text.startswith('{"error":'):
            return response_text

        # Otherwise, parse and validate the JSON response
        return self._parse_json_response(response_text)
