import pytest
from unittest.mock import Mock, patch
import time
from app.core.retry_utils import (
    RetryConfig,
    RetryHandler,
    RetryError,
    create_error_response,
    create_rate_limit_error
)


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
        assert config.initial_delay == 1.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=1.5,
            max_delay=30.0,
            backoff_multiplier=1.5,
            jitter=False,
            initial_delay=0.5
        )
        assert config.max_retries == 5
        assert config.base_delay == 1.5
        assert config.max_delay == 30.0
        assert config.backoff_multiplier == 1.5
        assert config.jitter is False
        assert config.initial_delay == 0.5


class TestRetryHandler:
    """Test RetryHandler class."""
    
    def test_is_rate_limit_error(self):
        """Test rate limit error detection."""
        handler = RetryHandler()
        
        # Test various rate limit error messages
        assert handler.is_rate_limit_error("HTTP 429 Too Many Requests")
        assert handler.is_rate_limit_error("quota exceeded")
        assert handler.is_rate_limit_error("rate limit exceeded")
        assert handler.is_rate_limit_error("Too Many Requests")
        assert handler.is_rate_limit_error("Rate Limit")
        
        # Test non-rate limit errors
        assert not handler.is_rate_limit_error("HTTP 500 Internal Server Error")
        assert not handler.is_rate_limit_error("Connection timeout")
        assert not handler.is_rate_limit_error("Invalid JSON")
    
    def test_calculate_delay(self):
        """Test delay calculation."""
        config = RetryConfig(
            base_delay=2.0,
            backoff_multiplier=2.0,
            initial_delay=1.0,
            max_delay=10.0,
            jitter=False  # Disable jitter for predictable testing
        )
        handler = RetryHandler(config)
        
        # Test initial delay
        assert handler.calculate_delay(0) == 1.0
        
        # Test exponential backoff
        assert handler.calculate_delay(1) == 4.0  # base_delay * (backoff_multiplier ** 1) = 2.0 * 2^1 = 4.0
        assert handler.calculate_delay(2) == 8.0  # base_delay * (backoff_multiplier ** 2) = 2.0 * 2^2 = 8.0
        assert handler.calculate_delay(3) == 10.0  # base_delay * (backoff_multiplier ** 3) = 2.0 * 2^3 = 16.0, capped at 10.0
    
    @patch('time.sleep')
    def test_successful_operation(self, mock_sleep):
        """Test successful operation without retries."""
        handler = RetryHandler()
        
        def successful_operation():
            return "success"
        
        result = handler.execute_with_retry(successful_operation)
        assert result == "success"
        mock_sleep.assert_called_once_with(1.0)  # Initial delay
    
    @patch('time.sleep')
    def test_retry_on_rate_limit(self, mock_sleep):
        """Test retry behavior on rate limit errors."""
        config = RetryConfig(max_retries=3, initial_delay=0.1, base_delay=0.1)
        handler = RetryHandler(config)
        
        call_count = 0
        def rate_limited_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("HTTP 429 Too Many Requests")
            return "success"
        
        result = handler.execute_with_retry(rate_limited_operation)
        assert result == "success"
        assert call_count == 3
    
    @patch('time.sleep')
    def test_non_retryable_error(self, mock_sleep):
        """Test immediate failure on non-retryable errors."""
        handler = RetryHandler()
        
        def failing_operation():
            raise Exception("Invalid JSON")
        
        with pytest.raises(RetryError) as exc_info:
            handler.execute_with_retry(failing_operation)
        
        assert "Non-retryable error" in str(exc_info.value)
        assert exc_info.value.attempts == 1
    
    @patch('time.sleep')
    def test_exhausted_retries(self, mock_sleep):
        """Test behavior when all retries are exhausted."""
        config = RetryConfig(max_retries=2)
        handler = RetryHandler(config)
        
        def always_rate_limited():
            raise Exception("HTTP 429 Too Many Requests")
        
        with pytest.raises(RetryError) as exc_info:
            handler.execute_with_retry(always_rate_limited)
        
        assert "Rate limit exceeded after 2 attempts" in str(exc_info.value)
        assert exc_info.value.attempts == 2
    
    @patch('time.sleep')
    def test_error_handler(self, mock_sleep):
        """Test custom error handler."""
        handler = RetryHandler()
        
        def failing_operation():
            raise Exception("HTTP 429 Too Many Requests")
        
        def custom_error_handler(error_msg, attempts):
            return {"custom_error": error_msg, "attempts": attempts}
        
        result = handler.execute_with_retry(
            failing_operation,
            error_handler=custom_error_handler
        )
        
        assert result["custom_error"] == "HTTP 429 Too Many Requests"
        assert result["attempts"] == 3


class TestErrorResponseHelpers:
    """Test error response helper functions."""
    
    def test_create_error_response(self):
        """Test error response creation."""
        response = create_error_response("Test error", 3, "Test suggestion")
        
        assert response["error"] == "Test error"
        assert response["suggestion"] == "Test suggestion"
    
    def test_create_error_response_no_suggestion(self):
        """Test error response without suggestion."""
        response = create_error_response("Test error", 3)
        
        assert response["error"] == "Test error"
        assert "suggestion" not in response
    
    def test_create_rate_limit_error(self):
        """Test rate limit error response creation."""
        response = create_rate_limit_error(3)
        
        assert "Rate limit exceeded after 3 attempts" in response["error"]
        assert "suggestion" in response
