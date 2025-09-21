#!/usr/bin/env python3
"""
Test runner script for invest-svc microservice.
Supports multiple test frameworks and configurations.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    success, stdout, stderr = run_command("pip install -r requirements-test.txt")
    if not success:
        print(f"Error installing dependencies: {stderr}")
        return False
    print("Dependencies installed successfully")
    return True

def run_unittest_tests():
    """Run unittest-based tests."""
    print("\n" + "="*50)
    print("Running unittest-based tests...")
    print("="*50)
    
    # Run unit tests
    success, stdout, stderr = run_command("python -m unittest test_invest_svc_unit.py -v")
    if not success:
        print(f"Unit tests failed: {stderr}")
        return False
    
    print("Unit tests passed!")
    return True

def run_pytest_tests(coverage=False, html=False, parallel=False):
    """Run pytest-based tests."""
    print("\n" + "="*50)
    print("Running pytest-based tests...")
    print("="*50)
    
    # Build pytest command
    cmd_parts = ["python -m pytest"]
    
    if parallel:
        cmd_parts.append("-n auto")
    
    if coverage:
        cmd_parts.append("--cov=invest_src --cov-report=term-missing")
    
    if html:
        cmd_parts.append("--html=test_report.html --self-contained-html")
    
    cmd_parts.append("test_invest_svc_pytest.py -v")
    
    command = " ".join(cmd_parts)
    success, stdout, stderr = run_command(command)
    
    if not success:
        print(f"Pytest tests failed: {stderr}")
        return False
    
    print("Pytest tests passed!")
    return True

def run_integration_tests():
    """Run integration tests."""
    print("\n" + "="*50)
    print("Running integration tests...")
    print("="*50)
    
    # Check if test database is available
    test_db_uri = os.getenv('TEST_DB_URI', 'postgresql://test:test@localhost:5432/test_invest_db')
    print(f"Using test database: {test_db_uri}")
    
    success, stdout, stderr = run_command("python test_invest_svc_integration.py")
    if not success:
        print(f"Integration tests failed: {stderr}")
        return False
    
    print("Integration tests passed!")
    return True

def run_linting():
    """Run code linting."""
    print("\n" + "="*50)
    print("Running code linting...")
    print("="*50)
    
    # Run flake8
    success, stdout, stderr = run_command("flake8 ../invest_src.py --max-line-length=120")
    if not success:
        print(f"Flake8 issues found: {stderr}")
        return False
    
    # Run black check
    success, stdout, stderr = run_command("black --check ../invest_src.py")
    if not success:
        print(f"Black formatting issues found: {stderr}")
        return False
    
    # Run isort check
    success, stdout, stderr = run_command("isort --check-only ../invest_src.py")
    if not success:
        print(f"Import sorting issues found: {stderr}")
        return False
    
    print("Linting passed!")
    return True

def run_type_checking():
    """Run type checking with mypy."""
    print("\n" + "="*50)
    print("Running type checking...")
    print("="*50)
    
    success, stdout, stderr = run_command("mypy ../invest_src.py --ignore-missing-imports")
    if not success:
        print(f"Type checking issues found: {stderr}")
        return False
    
    print("Type checking passed!")
    return True

def run_performance_tests():
    """Run performance tests."""
    print("\n" + "="*50)
    print("Running performance tests...")
    print("="*50)
    
    success, stdout, stderr = run_command("python -m pytest test_invest_svc_pytest.py::TestInvestSvcPerformance -v --benchmark-only")
    if not success:
        print(f"Performance tests failed: {stderr}")
        return False
    
    print("Performance tests passed!")
    return True

def generate_test_report():
    """Generate comprehensive test report."""
    print("\n" + "="*50)
    print("Generating test report...")
    print("="*50)
    
    report = {
        "service": "invest-svc",
        "test_framework": "pytest + unittest",
        "coverage": "enabled",
        "linting": "enabled",
        "type_checking": "enabled",
        "performance": "enabled"
    }
    
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("Test report generated: test_report.json")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for invest-svc microservice")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--pytest", action="store_true", help="Run pytest tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--type-check", action="store_true", help="Run type checking only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting")
    parser.add_argument("--html", action="store_true", help="Generate HTML test report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    
    args = parser.parse_args()
    
    # Change to tests directory
    os.chdir(Path(__file__).parent)
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)
    
    # Run specific test types
    if args.unit:
        if not run_unittest_tests():
            sys.exit(1)
    elif args.integration:
        if not run_integration_tests():
            sys.exit(1)
    elif args.pytest:
        if not run_pytest_tests(args.coverage, args.html, args.parallel):
            sys.exit(1)
    elif args.lint:
        if not run_linting():
            sys.exit(1)
    elif args.type_check:
        if not run_type_checking():
            sys.exit(1)
    elif args.performance:
        if not run_performance_tests():
            sys.exit(1)
    elif args.all:
        # Run all tests
        print("Running comprehensive test suite...")
        
        if not install_test_dependencies():
            sys.exit(1)
        
        if not run_linting():
            sys.exit(1)
        
        if not run_type_checking():
            sys.exit(1)
        
        if not run_unittest_tests():
            sys.exit(1)
        
        if not run_pytest_tests(args.coverage, args.html, args.parallel):
            sys.exit(1)
        
        if not run_integration_tests():
            sys.exit(1)
        
        if not run_performance_tests():
            sys.exit(1)
        
        generate_test_report()
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print("="*50)
    else:
        # Default: run pytest tests with coverage
        if not run_pytest_tests(True, False, False):
            sys.exit(1)

if __name__ == "__main__":
    main()
