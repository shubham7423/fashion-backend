"""
Retry utility with exponential backoff for API calls.

This module provides a reusable retry mechanism with exponential backoff
and jitter for handling rate limits and transient errors in API calls.
"""

import time
import random
import json
from typing import Callable, Any, Optional
from app.core.logging_config import get_logger


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        initial_delay: float = 1.0
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay cap in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            initial_delay: Delay before first attempt in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.initial_delay = initial_delay


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


class RetryHandler:
    """Handles retry logic with exponential backoff for API calls."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry handler.
        
        Args:
            config: Retry configuration, uses defaults if None
        """
        self.config = config or RetryConfig()
    
    def is_rate_limit_error(self, error_message: str) -> bool:
        """
        Check if the error is a rate limit error.
        
        Args:
            error_message: Error message to check
            
        Returns:
            bool: True if it's a rate limit error
        """
        error_lower = error_message.lower()
        return (
            "429" in error_message
            or "quota" in error_lower
            or "rate" in error_lower
            or "too many requests" in error_lower
            or "rate limit" in error_lower
        )
    
    def is_retryable_error(self, error_message: str) -> bool:
        """
        Check if the error is retryable (rate limit or transient errors).
        
        Args:
            error_message: Error message to check
            
        Returns:
            bool: True if the error is retryable
        """
        return self.is_rate_limit_error(error_message)
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt number.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            float: Delay in seconds
        """
        if attempt == 0:
            return self.config.initial_delay
        
        # Exponential backoff
        delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        
        # Apply jitter if enabled
        if self.config.jitter:
            delay += random.uniform(0, 1)
        
        # Cap the delay
        return min(delay, self.config.max_delay)
    
    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        error_handler: Optional[Callable[[str, int], Any]] = None,
        context: str = "operation"
    ) -> Any:
        """
        Execute an operation with retry attempts using the instance's retry configuration (exponential backoff, optional jitter).
        
        Parameters:
            operation (Callable[[], Any]): A zero-argument callable to execute. Its return value is returned on success.
            error_handler (Optional[Callable[[str, int], Any]]): Optional callback invoked on failure with the error message and the attempt count (1-based for non-retryable errors, or max_retries when rate limits are exhausted). If provided, its return value will be returned instead of raising.
            context (str): Short description of the operation used in error messages and logging.
        
        Returns:
            Any: The successful result of `operation`, or the value returned by `error_handler` when provided.
        
        Raises:
            RetryError: If retries are exhausted for retryable errors or a non-retryable error occurs and no `error_handler` is supplied.
        """
        logger = get_logger(__name__)
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                delay = self.calculate_delay(attempt)
                if delay > 0:
                    if attempt > 0:
                        logger.warning(
                            f"Rate limit hit for {context}, waiting {delay:.1f} seconds "
                            f"before retry {attempt + 1}/{self.config.max_retries}..."
                        )
                    time.sleep(delay)
                return operation()
            except Exception as e:
                last_error = e
                error_message = str(e)
                if self.is_retryable_error(error_message):
                    if attempt < self.config.max_retries - 1:
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {self.config.max_retries} attempts for {context}")
                        if error_handler:
                            return error_handler(error_message, self.config.max_retries)
                        else:
                            raise RetryError(
                                f"Rate limit exceeded after {self.config.max_retries} attempts for {context}",
                                self.config.max_retries,
                                last_error
                            )
                else:
                    if error_handler:
                        return error_handler(error_message, attempt + 1)
                    else:
                        logger.error(f"Non-retryable error in {context}: {error_message}")
                        raise RetryError(
                            f"Non-retryable error in {context}: {error_message}",
                            attempt + 1,
                            last_error
                        )
        if error_handler:
            return error_handler("Unexpected error in retry loop", self.config.max_retries)
        else:
            logger.error(f"Unexpected error in retry loop for {context}")
            raise RetryError(
                f"Unexpected error in retry loop for {context}",
                self.config.max_retries,
                last_error
            )


def create_error_response(error_message: str, max_retries: int, suggestion: str = None) -> dict:
    """
    Create a standardized error response dictionary.
    
    Args:
        error_message: The error message
        max_retries: Number of attempts made
        suggestion: Optional suggestion for the user
        
    Returns:
        dict: Error response dictionary
    """
    response = {"error": error_message}
    if suggestion:
        response["suggestion"] = suggestion
    return response


def create_rate_limit_error(max_retries: int) -> dict:
    """
    Create a standardized rate limit error response.
    
    Args:
        max_retries: Number of attempts made
        
    Returns:
        dict: Rate limit error response
    """
    return create_error_response(
        f"Rate limit exceeded after {max_retries} attempts. Please wait a few minutes before trying again.",
        max_retries,
        "Consider processing requests in smaller batches or with longer intervals between requests."
    )