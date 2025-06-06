#!/usr/bin/env python3
"""
Test Runner for Teaching Assistant

Convenient script to run different test suites with common configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Teaching Assistant Test Runner")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "debug", "all", "coverage"],
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", "-f", help="Specific test file to run")

    args = parser.parse_args()

    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        base_cmd.append("-v")

    # Determine test path and description
    if args.file:
        test_path = (
            f"tests/{args.file}" if not args.file.startswith("tests/") else args.file
        )
        description = f"Running specific test: {args.file}"
        cmd = base_cmd + [test_path]
    elif args.test_type == "unit":
        cmd = base_cmd + ["tests/unit/"]
        description = "Running unit tests"
    elif args.test_type == "integration":
        cmd = base_cmd + ["tests/integration/"]
        description = "Running integration tests"
    elif args.test_type == "debug":
        print("🔧 Debug scripts should be run individually:")
        debug_scripts = list(Path("tests/debug").glob("*.py"))
        for script in debug_scripts:
            if script.name != "__init__.py":
                print(f"  python {script}")
        return 0
    elif args.test_type == "coverage":
        cmd = base_cmd + [
            "--cov=api",
            "--cov=lib",
            "--cov-report=html",
            "--cov-report=term-missing",
            "tests/unit/",
            "tests/integration/",
        ]
        description = "Running tests with coverage"
    else:  # all
        cmd = base_cmd + ["tests/unit/", "tests/integration/"]
        description = "Running all tests"

    # Run the tests
    success = run_command(cmd, description)

    if args.test_type == "coverage" and success:
        print("\n📊 Coverage report generated in htmlcov/index.html")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
