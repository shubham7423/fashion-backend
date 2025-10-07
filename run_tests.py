#!/usr/bin/env python3
"""
Enhanced test runner for the Fashion Backend API

Supports running different categories of tests with various options.
"""

import subprocess
import sys
import argparse
import logging
from pathlib import Path

# Setup basic logging for the test runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_pytest(args_list, description="Running tests"):
    """Run pytest with given arguments."""
    logger.info(f"Starting: {description}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + args_list,
            cwd=Path(__file__).parent,
            capture_output=False,
        )
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully!")
        else:
            logger.error(f"❌ {description} failed with return code: {result.returncode}")
        return result.returncode
    except FileNotFoundError:
        logger.error("❌ pytest not found. Please install it first:")
        logger.error("   pip install pytest pytest-asyncio pytest-cov pytest-mock")
        return 1
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Fashion Backend API Test Runner")
    
    # Test category options
    parser.add_argument(
        "--unit", action="store_true",
        help="Run only unit tests (fast, isolated)"
    )
    parser.add_argument(
        "--integration", action="store_true", 
        help="Run only integration tests (requires API server)"
    )
    parser.add_argument(
        "--performance", action="store_true",
        help="Run only performance tests"
    )
    parser.add_argument(
        "--slow", action="store_true",
        help="Run slow tests (AI API calls, large files)"
    )
    
    # Test markers
    parser.add_argument(
        "--api", action="store_true",
        help="Run only API endpoint tests"
    )
    parser.add_argument(
        "--service", action="store_true",
        help="Run only service layer tests"
    )
    parser.add_argument(
        "--model", action="store_true",
        help="Run only model tests"
    )
    parser.add_argument(
        "--error-handling", action="store_true",
        help="Run only error handling tests"
    )
    
    # Coverage options
    parser.add_argument(
        "--coverage", action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--coverage-html", action="store_true",
        help="Generate HTML coverage report"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Quiet output"
    )
    parser.add_argument(
        "--failed-first", action="store_true",
        help="Run failed tests first"
    )
    
    # Additional pytest options
    parser.add_argument(
        "--pattern", type=str,
        help="Run tests matching pattern (e.g., 'test_model')"
    )
    parser.add_argument(
        "--file", type=str,
        help="Run specific test file"
    )
    
    args = parser.parse_args()
    
    # Build pytest arguments
    pytest_args = []
    
    # Test selection
    if args.unit:
        pytest_args.extend(["-m", "unit", "tests/unit/"])
        description = "Unit tests"
    elif args.integration:
        pytest_args.extend(["-m", "integration", "tests/integration/"])
        description = "Integration tests"
    elif args.performance:
        pytest_args.extend(["-m", "performance", "tests/performance/"])
        description = "Performance tests"
    elif args.slow:
        pytest_args.extend(["-m", "slow"])
        description = "Slow tests"
    elif args.api:
        pytest_args.extend(["-m", "api"])
        description = "API tests"
    elif args.service:
        pytest_args.extend(["-m", "service"])
        description = "Service tests"
    elif args.model:
        pytest_args.extend(["-m", "model"])
        description = "Model tests"
    elif args.error_handling:
        pytest_args.extend(["-m", "error_handling"])
        description = "Error handling tests"
    elif args.file:
        pytest_args.append(f"tests/{args.file}")
        description = f"Tests in {args.file}"
    elif args.pattern:
        pytest_args.extend(["-k", args.pattern])
        description = f"Tests matching '{args.pattern}'"
    else:
        pytest_args.extend(["-m", "not slow", "tests/"])
        description = "All tests (excluding slow tests)"
    
    logger.info(f"Selected test category: {description}")
    
    # Coverage options
    if args.coverage or args.coverage_html:
        pytest_args.extend(["--cov=app", "--cov-report=term"])
        if args.coverage_html:
            pytest_args.append("--cov-report=html")
    
    # Output options
    if args.verbose:
        pytest_args.append("-v")
    elif args.quiet:
        pytest_args.append("-q")
    else:
        pytest_args.append("-v")  # Default to verbose
    
    if args.failed_first:
        pytest_args.append("--failed-first")
    
    # Always add short traceback for better readability
    pytest_args.append("--tb=short")
    
    return run_pytest(pytest_args, description)


def run_tests():
    """Legacy function for backward compatibility."""
    return run_pytest(["-m", "not slow", "tests/", "-v", "--tb=short"], "All tests (excluding slow tests)")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run default tests
        exit_code = run_tests()
    else:
        # Parse arguments and run specific tests
        exit_code = main()
    
    sys.exit(exit_code)
