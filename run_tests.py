#!/usr/bin/env python3
"""
Test runner script for the LLM Benchmark Framework.

This script provides convenient ways to run tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle the output."""
    if description:
        print(f"\n🔄 {description}")
        print("=" * 50)
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = ["python3", "-m", "pytest", "tests/", "-m", "unit"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["python3", "-m", "pytest", "tests/", "-m", "integration"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = ["python3", "-m", "pytest", "tests/"]
    if verbose:
        cmd.append("-v")
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd, "Running all tests")


def run_specific_test(test_path, verbose=False):
    """Run a specific test."""
    cmd = ["python3", "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running test: {test_path}")


def run_linting():
    """Run linting checks."""
    success = True
    
    # Run flake8
    if not run_command(["python3", "-m", "flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"], "Running flake8 linting"):
        success = False
    
    # Run pylint on main modules
    for module in ["models", "metrics"]:
        if not run_command(["python3", "-m", "pylint", module, "--fail-under=8"], f"Running pylint on {module}"):
            success = False
    
    return success


def run_type_checking():
    """Run type checking."""
    return run_command(["python3", "-m", "mypy", "models", "metrics", "--ignore-missing-imports"], "Running type checking")


def install_dependencies():
    """Install test dependencies."""
    return run_command(["pip", "install", "-r", "requirements.txt"], "Installing dependencies")


def generate_coverage_report():
    """Generate a detailed coverage report."""
    cmd = ["python", "-m", "pytest", "tests/", "--cov", "--cov-report=html", "--cov-report=term"]
    return run_command(cmd, "Generating coverage report")


def main():
    parser = argparse.ArgumentParser(description="Test runner for LLM Benchmark Framework")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", type=str, help="Run specific test file or function")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--install", action="store_true", help="Install dependencies")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--quick", action="store_true", help="Quick test run (unit tests only, no coverage)")
    parser.add_argument("--ci", action="store_true", help="CI mode (all checks)")
    
    args = parser.parse_args()
    
    # If no specific command is given, show help
    if not any([args.unit, args.integration, args.all, args.test, args.lint, 
                args.type_check, args.coverage, args.install, args.quick, args.ci]):
        parser.print_help()
        return
    
    success = True
    
    # Install dependencies if requested
    if args.install:
        if not install_dependencies():
            success = False
    
    # Quick mode - just run unit tests
    if args.quick:
        if not run_unit_tests(verbose=args.verbose, coverage=False):
            success = False
    
    # CI mode - run all checks
    elif args.ci:
        print("🚀 Running full CI pipeline")
        print("=" * 50)
        
        # Install dependencies
        if not install_dependencies():
            success = False
        
        # Run linting
        if not run_linting():
            success = False
        
        # Run type checking
        if not run_type_checking():
            success = False
        
        # Run all tests with coverage
        if not run_all_tests(verbose=args.verbose, coverage=True):
            success = False
    
    else:
        # Run specific test types
        if args.unit:
            if not run_unit_tests(verbose=args.verbose, coverage=args.coverage):
                success = False
        
        if args.integration:
            if not run_integration_tests(verbose=args.verbose):
                success = False
        
        if args.all:
            if not run_all_tests(verbose=args.verbose, coverage=args.coverage):
                success = False
        
        if args.test:
            if not run_specific_test(args.test, verbose=args.verbose):
                success = False
        
        if args.lint:
            if not run_linting():
                success = False
        
        if args.type_check:
            if not run_type_checking():
                success = False
        
        if args.coverage:
            if not generate_coverage_report():
                success = False
    
    # Final status
    if success:
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 