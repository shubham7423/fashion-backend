from abc import ABC, abstractmethod
from app.core.retry_utils import RetryHandler, RetryConfig, create_rate_limit_error
import json


class Styler(ABC):

    def get_prompt_text(
        self,
        clothes_attributes,
        city="Toronto",
        weather="early fall weather - expect temperatures around 15-20°C, partly cloudy",
        occasion="casual day out",
    ) -> str:
        """Get the standardized prompt text for all models"""
        return f"""You are an expert AI fashion stylist with deep knowledge of color theory, seasonal trends, and style coordination. I will provide you with a JSON list of clothing items available in my digital closet.

Your task is to create a stylish, modern, and coherent outfit suitable for a '{occasion} in {city}'. The weather conditions are: {weather}.

Here is my closet (JSON format):
---
{clothes_attributes}
---

ADVANCED STYLING GUIDELINES:
🎨 COLOR COORDINATION:
- Prioritize complementary or analogous color schemes
- Consider neutral bases with one accent color
- Avoid clashing patterns unless intentionally eclectic
- Account for undertones (warm vs cool) in color matching

👗 FIT & SILHOUETTE:
- Balance proportions (fitted top with relaxed bottom, or vice versa)
- Consider layering potential for fall weather
- Ensure the outfit flatters different body types

🌟 STYLE HARMONY:
- Match formality levels (don't mix overly casual with formal)
- Consider fabric textures and how they work together
- Think about the overall aesthetic (minimalist, bohemian, classic, etc.)

☀️ SEASONAL APPROPRIATENESS:
- Choose weather-appropriate pieces for the specified conditions
- Layer-friendly pieces are ideal for variable weather
- Consider transitional pieces that work in changing weather

SELECTION RULES:
1. MANDATORY: Select exactly one 'top' and one 'bottom' from the provided list
2. OPTIONAL: Include an 'outerwear' piece if it enhances the outfit or suits the weather
3. STRICT REQUIREMENT: Only use items that exist in the provided JSON list
4. IMAGE PRECISION: Use the EXACT "image" field value from selected items
5. NO SHOES: The list contains no footwear, so don't include shoes in selections
6. JSON ONLY: Your response must be pure JSON with no additional text

Required output format (valid JSON only):
{{
    "top": "exact_image_filename_from_top_item",
    "bottom": "exact_image_filename_from_bottom_item",
    "outerwear": "exact_image_filename_from_outerwear_item_or_null",
    "justification": "Short explanation of why this outfit works together (color theory, fit, occasion suitability)",
    "style_notes": "Short Professional styling tips about why this combination works (textures, proportions, versatility)",
    "other_accessories": "Specific accessory recommendations (jewelry, bags, scarves) that would complete this look",
    "weather_consideration": "How this outfit addresses the specified weather conditions"
}}

CRITICAL REMINDER: Use exact "image" field values from the JSON items. For example, if selecting an item with "image": "top_1_shirt.jpg", use exactly "top_1_shirt.jpg" in your response.

Generate ONLY the JSON response now:"""

    def _retry_with_backoff(self, operation_func, max_retries=3, base_delay=2):
        """
        Execute an operation with retry logic and exponential backoff.

        Args:
            operation_func: Function to execute that returns the response text
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds

        Returns:
            str: Response text from the operation
        """
        # Configure retry behavior
        retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
            initial_delay=1.0
        )
        retry_handler = RetryHandler(retry_config)
        
        def error_handler(error_message: str, attempts: int) -> str:
            """Handle errors from styling operations."""
            if retry_handler.is_rate_limit_error(error_message):
                error_response = create_rate_limit_error(attempts)
                return json.dumps(error_response)
            else:
                return json.dumps({"error": f"Failed to generate outfit: {error_message}"})
        
        try:
            return retry_handler.execute_with_retry(
                operation_func,
                error_handler,
                context="outfit styling"
            )
        except Exception as e:
            # Fallback error handling
            return json.dumps({"error": f"Unexpected error in styling: {str(e)}"})

    def _is_rate_limit_error(self, error_message: str) -> bool:
        """Check if the error is a rate limit error (deprecated - use RetryHandler)."""
        retry_handler = RetryHandler()
        return retry_handler.is_rate_limit_error(error_message)

    def _create_rate_limit_error_response(self, max_retries: int) -> str:
        """Create a standardized rate limit error response (deprecated - use create_rate_limit_error)."""
        error_response = create_rate_limit_error(max_retries)
        return json.dumps(error_response)

    def _parse_json_response(self, response_text: str) -> str:
        """
        Parse and validate JSON response from the model.

        Args:
            response_text: Raw response text from the model

        Returns:
            str: Validated JSON string
        """
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
                return json.dumps(
                    {
                        "error": "Could not parse JSON response from model",
                        "raw_response": response_text,
                    }
                )

    @abstractmethod
    def style(
        self,
        clothing_attributes: list,
        city: str = "Toronto",
        weather: str = "early fall weather - expect temperatures around 15-20°C, partly cloudy",
        occasion: str = "casual day out",
    ) -> str:
        pass
