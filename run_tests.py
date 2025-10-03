#!/usr/bin/env python3
"""
Simple test runner for the Fashion Backend API
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all unit tests"""
    print("Running Fashion Backend Unit Tests")
    print("=" * 50)

    # Get the project root directory
    project_root = Path(__file__).parent

    try:
        # Run pytest with simple output
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=project_root,
            capture_output=False,
        )

        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")

        return result.returncode

    except FileNotFoundError:
        print("❌ pytest not found. Please install it first:")
        print("   pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
