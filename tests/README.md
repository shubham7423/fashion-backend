# Fashion Backend API Test Suite

Comprehensive test suite for the Fashion Backend API with organized unit, integration, and performance tests.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Global test configuration and fixtures
├── README.md                      # This file
├── fixtures/                      # Shared test fixtures
│   ├── __init__.py
│   └── image_fixtures.py          # Image-related test fixtures
├── unit/                          # Unit tests - fast, isolated, no external dependencies
│   ├── __init__.py
│   ├── test_models.py             # Pydantic model tests
│   ├── test_config.py             # Configuration tests
│   ├── test_attribution_service.py # Attribution service tests
│   ├── test_attribution_service_error_handling.py # Error handling tests
│   ├── test_styler_service.py     # Styler service tests
│   ├── test_retry_utils.py        # Retry utility tests
│   ├── test_routes.py             # API route tests (mocked)
│   └── test_attributors.py        # Attributor implementation tests
├── integration/                   # Integration tests - test component interactions
│   ├── __init__.py
│   ├── test_api.py                # Full API integration tests
│   └── test_styler_api.py         # Styler-specific integration tests
└── performance/                   # Performance and load tests
    ├── __init__.py
    └── test_load_performance.py   # Load testing scenarios
```

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests
```bash
# Using the test runner script (recommended)
python run_tests.py

# Using pytest directly
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test Categories

#### Unit Tests Only (Fast)
```bash
pytest tests/unit/ -v
python run_tests.py --unit
```

#### Integration Tests Only
```bash
pytest tests/integration/ -v
python run_tests.py --integration
```

#### Performance Tests Only
```bash
pytest tests/performance/ -v
python run_tests.py --performance
```

### Run Specific Test Files
```bash
# Models and configuration
pytest tests/unit/test_models.py -v
pytest tests/unit/test_config.py -v

# Services
pytest tests/unit/test_attribution_service.py -v
pytest tests/unit/test_styler_service.py -v

# API routes
pytest tests/unit/test_routes.py -v

# Integration tests
pytest tests/integration/test_api.py -v
```

### Run Tests with Markers
```bash
# Run only fast tests
pytest -m "not slow" -v

# Run only API tests  
pytest -m "api" -v

# Run only service tests
pytest -m "service" -v
```

## Test Coverage

The test suite covers:

### Unit Tests (tests/unit/)
- **Models** (`test_models.py`): Pydantic model creation, validation, and serialization
- **Configuration** (`test_config.py`): Settings, environment variables, and defaults
- **Attribution Service** (`test_attribution_service.py`): Image validation, processing, compression
- **Attribution Error Handling** (`test_attribution_service_error_handling.py`): Error scenarios and recovery
- **Styler Service** (`test_styler_service.py`): User data processing, outfit recommendations
- **Retry Utils** (`test_retry_utils.py`): Retry logic, backoff strategies, error handling
- **Routes** (`test_routes.py`): API endpoints with mocked dependencies
- **Attributors** (`test_attributors.py`): AI service integrations (Gemini, etc.)

### Integration Tests (tests/integration/)
- **API Integration** (`test_api.py`): Full API workflow testing with real HTTP calls
- **Styler API** (`test_styler_api.py`): End-to-end styler functionality testing

### Performance Tests (tests/performance/)
- **Load Testing** (`test_load_performance.py`): Concurrent requests, response times
- **Memory Usage**: Memory profiling during image processing
- **Scalability**: Performance under various load conditions

## Test Categories and Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Fast unit tests with no external dependencies
- `@pytest.mark.integration`: Integration tests requiring API server
- `@pytest.mark.slow`: Long-running tests (AI API calls, large file processing)
- `@pytest.mark.api`: API endpoint tests
- `@pytest.mark.service`: Service layer tests
- `@pytest.mark.model`: Model and validation tests
- `@pytest.mark.performance`: Performance and load tests

## Test Environment Setup

### Environment Variables for Testing
```bash
# Create .env.test file
GEMINI_API_KEY="test_api_key_for_mocking"
OPENAI_API_KEY="test_api_key_for_mocking"
TARGET_WIDTH=256
TARGET_HEIGHT=256
MAX_FILE_SIZE=5242880  # 5MB for faster tests
```

### Test Data Management
- Temporary directories are created for each test session
- Test images are generated programmatically
- User data is mocked using fixtures
- No persistent test data is created

## Test Philosophy and Best Practices

### Unit Test Principles
- **Fast execution**: No external API calls, file I/O, or network requests
- **Isolated**: Each test is independent and can run in any order
- **Mocked dependencies**: External services and file systems are mocked
- **Single responsibility**: Each test validates one specific behavior
- **Clear naming**: Test names describe what is being tested and expected outcome

### Integration Test Principles
- **Real interactions**: Test actual API endpoints and service integrations
- **End-to-end workflows**: Validate complete user scenarios
- **External dependencies**: May use real AI APIs (with rate limiting considerations)
- **Environment validation**: Ensure the full system works together

### Performance Test Principles
- **Baseline measurements**: Establish performance benchmarks
- **Load simulation**: Test under realistic usage scenarios
- **Resource monitoring**: Track memory, CPU, and response times
- **Scalability validation**: Ensure system handles increased load

## Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests before each commit
pre-commit run --all-files
```

### CI Pipeline (GitHub Actions)
```yaml
# .github/workflows/tests.yml
- Unit tests: Run on every PR
- Integration tests: Run on main branch
- Performance tests: Run nightly
- Coverage reporting: Minimum 80% coverage required
```

## Debugging Tests

### Running Tests in Debug Mode
```bash
# Run with detailed output
pytest tests/ -v -s --tb=long

# Run specific failing test with debugging
pytest tests/unit/test_models.py::TestModels::test_specific_method -v -s --pdb

# Run with coverage and open HTML report
pytest tests/ --cov=app --cov-report=html && open htmlcov/index.html
```

### Common Test Issues
1. **Mocking not working**: Ensure import paths are correct
2. **Async test failures**: Use `@pytest.mark.asyncio` for async functions
3. **File path issues**: Use absolute paths in tests, mock file operations
4. **Environment variables**: Use fixtures to mock settings

## Contributing to Tests

### Adding New Tests
1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Use descriptive test class and method names
4. Add appropriate pytest markers
5. Mock external dependencies
6. Follow existing test patterns

### Test Naming Convention
```python
class TestServiceName:
    def test_method_name_expected_behavior(self):
        """Test that method_name does expected_behavior when given conditions."""
        # Arrange, Act, Assert
```
