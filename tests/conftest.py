"""Test configuration and fixtures for the Fashion Backend API tests."""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import fixtures from fixtures module
from tests.fixtures.image_fixtures import (
    sample_image_data,
    mock_upload_file,
    mock_pil_image,
    test_image_attributes,
    test_user_data,
    ImageTestFixtures
)


@pytest.fixture(scope="session")
def temp_data_dir():
    """Create a temporary directory for test data that lasts the entire test session."""
    temp_dir = tempfile.mkdtemp(prefix="fashion_backend_test_")
    yield Path(temp_dir)
    # Cleanup after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings():
    """Mock application settings for testing."""
    with patch('app.core.config.settings') as mock:
        mock.USER_DATA_DIRECTORY = "test_user_data"
        mock.ATTRIBUTES_JSON_FILE = "image_attributes.json"
        mock.CREATE_USER_SUBDIRS = True
        mock.SAVE_IMAGES = False
        mock.MAX_FILE_SIZE = 10 * 1024 * 1024
        mock.TARGET_WIDTH = 512
        mock.TARGET_HEIGHT = 512
        mock.JPEG_QUALITY = 85
        mock.MAINTAIN_ASPECT_RATIO = True
        mock.ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif"}
        mock.GEMINI_API_KEY = "test_api_key"
        mock.DEFAULT_STYLER = "gemini"
        yield mock


@pytest.fixture
def clean_test_environment(temp_data_dir, mock_settings):
    """Provide a clean test environment with temporary directories and mocked settings."""
    with patch('app.core.config.settings.USER_DATA_DIRECTORY', str(temp_data_dir)):
        yield {
            'temp_dir': temp_data_dir,
            'settings': mock_settings
        }


# Test markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests - fast, isolated, no external dependencies")
    config.addinivalue_line("markers", "integration: Integration tests - test component interactions")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "slow: Slow tests - may involve AI API calls or large files")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "service: Service layer tests")
    config.addinivalue_line("markers", "model: Model and validation tests")
    config.addinivalue_line("markers", "error_handling: Error handling and edge case tests")
    config.addinivalue_line("markers", "regression: Regression tests for bug fixes")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Mark tests based on test name patterns
        if "error" in item.name.lower() or "exception" in item.name.lower():
            item.add_marker(pytest.mark.error_handling)
        
        if "api" in item.name.lower() or "route" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        if "service" in item.name.lower():
            item.add_marker(pytest.mark.service)
        
        if "model" in item.name.lower():
            item.add_marker(pytest.mark.model)
