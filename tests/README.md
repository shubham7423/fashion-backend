# Unit Tests

Simple unit tests for the Fashion Backend API following the existing code structure.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration
├── test_models.py           # Pydantic model tests
├── test_config.py           # Configuration tests
├── test_attribution_service.py  # Attribution service tests
├── test_styler_service.py   # Styler service tests
└── test_attributors.py      # Attributor tests
```

## Running Tests

### Install test dependencies
```bash
pip install pytest
```

### Run all tests
```bash
# Using pytest directly
pytest tests/ -v

# Using the test runner script
python run_tests.py
```

### Run specific test files
```bash
pytest tests/test_models.py -v
pytest tests/test_config.py -v
```

## Test Coverage

The tests cover:

- **Models**: Pydantic model creation and validation
- **Configuration**: Settings and default values
- **Attribution Service**: Image validation, processing, and info creation
- **Styler Service**: User data processing and outfit recommendation logic
- **Attributors**: Base attributor and Gemini implementation

## Test Philosophy

These tests follow a simple approach:
- Focus on core functionality without unnecessary complexity
- Mock external dependencies (AI APIs, file system)
- Test public methods and key logic paths
- Verify expected data structures and responses
- Keep tests fast and reliable

## Notes

- Tests use mocking for external dependencies (Gemini API, OpenAI API)
- File system operations are mocked to avoid creating test files
- Tests focus on business logic rather than integration testing
- API integration tests are separate (`test_api.py`, `test_styler_api.py`)
