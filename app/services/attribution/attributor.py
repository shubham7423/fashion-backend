from abc import ABC, abstractmethod
from PIL import Image


class Attributor(ABC):
    def get_prompt_text(self) -> str:
        """Get the standardized prompt text for all models"""
        return """You are a fashion expert AI assistant. Analyze the clothing item in this image and provide its key attributes.
Your response MUST be a single, minified JSON object with no other text before or after it.

The JSON object should have the following keys:
- "identifier": Is it a top, bottom, dress, outerwear, shoes or accessory?
- "category": Identify the type of clothing. Examples: "T-Shirt", "Jeans", "Sweater", "Dress", "Jacket".
- "gender": Is it for men, women, or unisex?
- "primary_color": The dominant color. Be specific and accurate - use precise color names like "Navy", "Burgundy", "Forest Green", "Charcoal", "Cream", "Olive", "Maroon", "Teal", "Coral", "Beige" instead of generic terms like "Blue", "Red", "Green", "Gray", "White", "Yellow", "Pink", "Brown".
- "style": A descriptive style. Examples: "Casual", "Formal", "Sporty", "Minimalist", "Business Casual".
- "occasion": The suitable occasion. Examples: "Everyday", "Work", "Party", "Outdoor", "Formal Event".
- "weather": The appropriate weather. Examples: "Warm", "Cold", "Rainy", "Mild".
- "fit": The fit type. Examples: "Slim Fit", "Regular Fit", "Loose Fit", "Oversized".
- "sleeve_length": Sleeve length if applicable. Examples: "Short Sleeve", "Long Sleeve", "Sleeveless", "3/4 Sleeve".
- "description": A brief, one-sentence description of the item.

Analyze the provided image and generate the JSON now. Rules to read from the image:
- Focus on the main clothing item in the image.
- If multiple items are present, describe the most prominent one.
- If the item is not clearly visible, make your best guess based on visible features.
- Pay special attention to color accuracy - distinguish between similar shades (e.g., Navy vs Royal Blue, Charcoal vs Black, Cream vs White)."""

    @abstractmethod
    def extract(self, image: Image.Image, image_filename: str = None) -> dict:
        pass
