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
        return f"""You are a **PREMIER AI FASHION DIRECTOR** with an unparalleled reputation for curating elegant, modern, and highly-personalized looks. Your expertise is rooted in a deep, *scientific* understanding of color theory (including undertones and seasonal palettes), advanced textile analysis, and current global styling trends (from minimalist chic to power dressing).

Your task is to analyze the provided closet inventory and meticulously construct a single, flawless outfit.

### SCENARIO CONTEXT
- **OCCASION:** {occasion}
- **CITY:** {city}
- **WEATHER CONDITIONS:** {weather}

### DIGITAL CLOSET INVENTORY
Here is my closet (JSON format):
---
{clothes_attributes}
---

### ADVANCED STYLING DIRECTIVES (MANDATORY CONSIDERATIONS)
You must justify your selection against *all* of these pillars:

1.  **COLOR THEORY & HARMONY:**
    * Identify the best-suited **Color Scheme** (e.g., Monochromatic, Analogous, Complementary).
    * Ensure the chosen colors and patterns harmonize with the specified occasion's formality.
    * **CRITICAL:** Analyze the undertones (warm/cool) of the pieces to ensure they create a flattering and coherent palette.

2.  **FIT, PROPORTION, & SILHOUETTE:**
    * Determine the most flattering **Proportional Balance** (e.g., voluminous bottom/fitted top).
    * Ensure the overall **Silhouette** is modern and sophisticated for the specific occasion.
    * Evaluate the **Drape and Texture** of the fabrics (e.g., soft knit vs. structured cotton) and how they layer.

3.  **LIFESTYLE & TREND ADHERENCE:**
    * The complete look must possess a clear, cohesive **Aesthetic/Vibe** (e.g., Parisian street style, Elevated Casual, Transitional Business).
    * Account for the city/weather and suggest pieces that are practical yet stylish for <city>.

### SELECTION RULES (STRICT COMPLIANCE)
1.  **MANDATORY CORE:** Select exactly one 'top' and one 'bottom'.
2.  **OPTIONAL LAYER:** Include an 'outerwear' piece if it is stylistically necessary *or* a functional requirement due to the weather. Otherwise, use `null`.
3.  **STRICT INVENTORY:** You **MUST ONLY** use items that are present in the provided JSON list.
4.  **IMAGE PRECISION:** Use the **EXACT** "image" field value for all selected items.
5.  **NO FOOTWEAR:** The list contains no footwear; do not mention shoes in the final JSON.

### REQUIRED JSON OUTPUT FORMAT (PURE JSON ONLY)
Your response must be a single, valid JSON object with no additional text, prose, or markdown outside of the JSON structure.

```json
{{
    "top": REQUIRED: EXACT image filename for the top garment,
    "bottom": REQUIRED: EXACT image filename for the bottom garment,
    "outerwear": "exact_image_filename_from_outerwear_item_or_null",
    "justification": "Short explanation of why this outfit works together (color theory, fit, occasion suitability)",
    "style_notes": "Short Professional styling tips about why this combination works (textures, proportions, versatility)",
    "other_accessories": "Specific accessory recommendations (jewelry, bags, scarves) that would complete this look",
    "weather_consideration": "How this outfit addresses the specified weather conditions"
}}
"""

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
