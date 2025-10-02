import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json
from app.services.styler_service import StylerService
from app.models.response import StylerResponse


class TestStylerService:
    """Test StylerService functionality"""

    def test_get_user_json_file_path_with_subdirs(self):
        """Test user JSON file path generation with subdirectories"""
        with patch('app.core.config.settings.CREATE_USER_SUBDIRS', True):
            with patch('app.core.config.settings.USER_DATA_DIRECTORY', 'user_data'):
                with patch('app.core.config.settings.ATTRIBUTES_JSON_FILE', 'attributes.json'):
                    path = StylerService.get_user_json_file_path("test_user")
                    expected = Path("user_data") / "test_user" / "attributes.json"
                    assert path == expected

    def test_get_user_json_file_path_without_subdirs(self):
        """Test user JSON file path generation without subdirectories"""
        with patch('app.core.config.settings.CREATE_USER_SUBDIRS', False):
            with patch('app.core.config.settings.ATTRIBUTES_JSON_FILE', 'attributes.json'):
                path = StylerService.get_user_json_file_path("test_user")
                expected = Path("test_user_attributes.json")
                assert path == expected

    def test_extract_clothing_attributes_for_styling(self):
        """Test extraction of clothing attributes for styling"""
        user_data = {
            "images": {
                "hash1": {
                    "filename": "shirt.jpg",
                    "attributes": {
                        "image": "shirt.jpg",
                        "identifier": "top",
                        "category": "T-Shirt",
                        "gender": "men",
                        "primary_color": "blue",
                        "style": "casual"
                    }
                },
                "hash2": {
                    "filename": "pants.jpg",
                    "attributes": {
                        "image": "pants.jpg",
                        "identifier": "bottom",
                        "category": "Jeans",
                        "gender": "men",
                        "primary_color": "navy"
                    }
                },
                "hash3": {
                    "filename": "invalid.jpg",
                    "attributes": {
                        "identifier": "unknown",
                        "category": "unknown"
                    }
                }
            }
        }
        
        attributes = StylerService.extract_clothing_attributes_for_styling(user_data)
        
        # Should return 2 valid items (excluding the one with unknown identifier/category)
        assert len(attributes) == 2
        assert attributes[0]["image"] == "shirt.jpg"
        assert attributes[0]["identifier"] == "top"
        assert attributes[1]["image"] == "pants.jpg"
        assert attributes[1]["identifier"] == "bottom"

    def test_extract_clothing_attributes_empty_data(self):
        """Test extraction with empty user data"""
        user_data = {"images": {}}
        attributes = StylerService.extract_clothing_attributes_for_styling(user_data)
        assert len(attributes) == 0

    def test_validate_styling_parameters(self):
        """Test styling parameter validation"""
        params = StylerService.validate_styling_parameters(
            "New York",
            "cold weather",
            "business meeting"
        )
        
        assert params["city"] == "New York"
        assert params["weather"] == "cold weather"
        assert params["occasion"] == "business meeting"

    @patch('app.services.styler_service.StylerService.load_user_attributes')
    @patch('app.services.styler_service.GeminiStyler')
    @pytest.mark.asyncio
    async def test_generate_outfit_recommendation_success(self, mock_gemini_styler, mock_load_user):
        """Test successful outfit recommendation generation"""
        # Mock user data
        mock_load_user.return_value = {
            "images": {
                "hash1": {
                    "attributes": {
                        "image": "shirt.jpg",
                        "identifier": "top",
                        "category": "T-Shirt",
                        "gender": "men",
                        "primary_color": "blue"
                    }
                }
            }
        }
        
        # Mock styler
        mock_styler_instance = Mock()
        mock_styler_instance.style.return_value = '{"top": "shirt.jpg", "bottom": "pants.jpg"}'
        mock_gemini_styler.return_value = mock_styler_instance
        
        with patch('app.core.config.settings.DEFAULT_STYLER', 'gemini'):
            response = await StylerService.generate_outfit_recommendation("test_user")
        
        assert isinstance(response, StylerResponse)
        assert response.success is True
        assert response.user_id == "test_user"
        assert response.available_items_count == 1

    @patch('app.services.styler_service.StylerService.load_user_attributes')
    @pytest.mark.asyncio
    async def test_generate_outfit_recommendation_no_items(self, mock_load_user):
        """Test outfit recommendation with no valid items"""
        mock_load_user.return_value = {"images": {}}
        
        response = await StylerService.generate_outfit_recommendation("test_user")
        
        assert isinstance(response, StylerResponse)
        assert response.success is False
        assert response.available_items_count == 0
        assert "No valid clothing items found" in response.message
