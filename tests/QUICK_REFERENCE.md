# Test Suite Quick Reference

## Available Test Commands

### Basic Usage
```bash
# Run all tests (excluding slow ones)
python run_tests.py

# Run all tests including slow ones
python run_tests.py --slow
```

### By Test Category
```bash
# Unit tests only (fast, isolated)
python run_tests.py --unit

# Integration tests only (requires API server)
python run_tests.py --integration  

# Performance tests only
python run_tests.py --performance
```

### By Component
```bash
# API endpoint tests
python run_tests.py --api

# Service layer tests  
python run_tests.py --service

# Model tests
python run_tests.py --model

# Error handling tests
python run_tests.py --error-handling
```

### With Coverage
```bash
# Text coverage report
python run_tests.py --coverage

# HTML coverage report
python run_tests.py --coverage-html
```

### Specific Files or Patterns
```bash
# Run specific test file
python run_tests.py --file unit/test_models.py

# Run tests matching pattern
python run_tests.py --pattern "test_model"
```

### Direct pytest Usage
```bash
# All unit tests
pytest tests/unit/ -v

# Specific markers
pytest -m "unit and not slow" -v
pytest -m "integration" -v
pytest -m "error_handling" -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Organization Summary

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # End-to-end API tests  
├── performance/    # Load and performance tests
└── fixtures/       # Shared test data
```

## Test Markers

- `unit`: Fast, isolated unit tests
- `integration`: Tests requiring API server
- `performance`: Performance and load tests
- `slow`: Tests that may take longer
- `api`: API endpoint tests
- `service`: Service layer tests
- `model`: Model validation tests
- `error_handling`: Error scenarios
