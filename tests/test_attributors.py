import pytest
from unittest.mock import Mock, patch
from app.services.attribution.attributor import Attributor
from app.services.attribution.gemini_attributor import GeminiAttributor
from PIL import Image


class TestAttributor:
    """Test Attributor base class"""

    def test_get_prompt_text(self):
        """Test prompt text generation"""

        # Create a concrete implementation for testing
        class TestAttributor(Attributor):
            def extract(self, image, image_filename=None):
                return {}

        attributor = TestAttributor()
        prompt = attributor.get_prompt_text()

        assert isinstance(prompt, str)
        assert "fashion expert ai assistant" in prompt.lower()
        assert "json" in prompt.lower()
        assert "identifier" in prompt
        assert "category" in prompt
        assert "primary_color" in prompt


class TestGeminiAttributor:
    """Test GeminiAttributor functionality"""

    @patch("app.core.config.settings.GEMINI_API_KEY", "test_key")
    @patch("google.generativeai.configure")
    @patch("google.generativeai.GenerativeModel")
    def test_gemini_attributor_initialization(self, mock_model, mock_configure):
        """Test GeminiAttributor initialization"""
        attributor = GeminiAttributor()

        mock_configure.assert_called_once_with(api_key="test_key")
        mock_model.assert_called_once_with("gemini-2.0-flash")

    def test_gemini_attributor_no_api_key(self):
        """Test GeminiAttributor initialization without API key"""
        with patch("app.core.config.settings.GEMINI_API_KEY", ""):
            with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
                GeminiAttributor()

    @patch("app.core.config.settings.GEMINI_API_KEY", "test_key")
    @patch("google.generativeai.configure")
    @patch("google.generativeai.GenerativeModel")
    def test_extract_successful_response(self, mock_model_class, mock_configure):
        """Test successful attribute extraction"""
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = (
            '{"identifier": "top", "category": "T-Shirt", "primary_color": "blue"}'
        )
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        attributor = GeminiAttributor()
        test_image = Image.new("RGB", (100, 100), color="red")

        result = attributor.extract(test_image, "test.jpg")

        assert isinstance(result, dict)
        assert result["identifier"] == "top"
        assert result["category"] == "T-Shirt"
        assert result["primary_color"] == "blue"
        assert result["image"] == "test.jpg"
