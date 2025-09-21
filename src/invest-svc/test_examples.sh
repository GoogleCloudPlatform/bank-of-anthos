#!/bin/bash
# Test examples for invest-svc microservice

echo "=========================================="
echo "Invest-SVC Testing Examples"
echo "=========================================="

# Change to tests directory
cd tests

echo ""
echo "1. Quick Test (No Dependencies)"
echo "================================"
python quick_test.py

echo ""
echo "2. Unit Tests (unittest framework)"
echo "==================================="
python -m unittest test_invest_svc_unit.py -v

echo ""
echo "3. Unit Tests (pytest framework)"
echo "================================="
pytest test_invest_svc_pytest.py -v

echo ""
echo "4. Integration Tests (requires database)"
echo "========================================"
echo "Note: Requires PostgreSQL database running"
echo "Set TEST_DB_URI environment variable"
# python test_invest_svc_integration.py

echo ""
echo "5. All Tests with Coverage"
echo "==========================="
pytest test_invest_svc_pytest.py --cov=invest_src --cov-report=html --cov-report=term

echo ""
echo "6. Performance Tests"
echo "===================="
pytest test_invest_svc_pytest.py::TestInvestSvcPerformance -v --benchmark-only

echo ""
echo "7. Linting and Code Quality"
echo "============================"
flake8 ../invest_src.py --max-line-length=120
black --check ../invest_src.py
isort --check-only ../invest_src.py

echo ""
echo "8. Docker-based Testing"
echo "======================="
echo "Build and run tests in Docker:"
echo "docker build -f Dockerfile.test -t invest-svc-test ."
echo "docker run --rm invest-svc-test"

echo ""
echo "9. Docker Compose Testing"
echo "========================="
echo "Run full test environment:"
echo "docker-compose -f docker-compose.test.yml up --build"

echo ""
echo "10. Test Runner Script"
echo "======================"
echo "Run comprehensive test suite:"
echo "python run_tests.py --all"

echo ""
echo "=========================================="
echo "Testing Examples Complete"
echo "=========================================="
