#!/bin/bash

# Copyright 2024 Google LLC
# Queue-DB Test Runner Script

echo "🧪 Queue-DB Test Suite Runner"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUEUE_DB_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Test Directory: $SCRIPT_DIR${NC}"
echo -e "${BLUE}Queue-DB Directory: $QUEUE_DB_DIR${NC}"

# Function to print test results
print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            echo -e "${GREEN}Docker is available and running${NC}"
            return 0
        else
            echo -e "${YELLOW}Docker is installed but not running${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Docker is not available${NC}"
        return 1
    fi
}

# Run Docker tests
run_docker_tests() {
    echo -e "\n${YELLOW}=== Running Docker Tests ===${NC}"
    cd "$SCRIPT_DIR"
    ./test_queue_db_docker.sh
    return $?
}

# Run SQL tests (manual commands)
run_sql_tests() {
    echo -e "\n${YELLOW}=== Running SQL Test Commands ===${NC}"
    cd "$SCRIPT_DIR"
    ./test_queue_db_sql.sh
    return $?
}

# Main execution
main() {
    echo -e "\n${YELLOW}Step 1: Checking Environment${NC}"
    
    if check_docker; then
        echo -e "\n${YELLOW}Step 2: Running Docker Tests${NC}"
        run_docker_tests
        docker_exit_code=$?
        
        if [ $docker_exit_code -eq 0 ]; then
            print_test 0 "Docker tests completed successfully"
        else
            print_test 1 "Docker tests failed"
        fi
    else
        echo -e "\n${YELLOW}Step 2: Docker not available, showing SQL test commands${NC}"
        run_sql_tests
        print_test 0 "SQL test commands displayed"
    fi
    
    echo -e "\n${YELLOW}Step 3: Test Summary${NC}"
    echo -e "${BLUE}Test files available:${NC}"
    echo "  - $SCRIPT_DIR/test_queue_db_docker.sh"
    echo "  - $SCRIPT_DIR/test_queue_db_sql.sh"
    
    echo -e "\n${GREEN}🎉 Queue-DB Test Suite Complete!${NC}"
    echo "=============================="
}

# Run main function
main "$@"
