#!/usr/bin/env python3
"""
Simple Queue-DB Test Script
Tests the queue-db schema and functionality without Docker
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def print_test(name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {name}")
    if details:
        print(f"    Details: {details}")

def main():
    print("🧪 Queue-DB Simple Test Suite")
    print("=" * 40)
    
    # Test 1: Check if Docker is available
    print("\n1. Checking Docker availability...")
    success, stdout, stderr = run_command("docker --version")
    print_test("Docker Available", success, stdout if success else stderr)
    
    if not success:
        print("\n❌ Docker not available. Please install Docker to run comprehensive tests.")
        print("📋 You can run the SQL test commands manually:")
        print("   - See test_queue_db_sql.sh for manual testing commands")
        return
    
    # Test 2: Check if we can build the Docker image
    print("\n2. Building Queue-DB Docker image...")
    os.chdir("..")  # Go to queue-db directory
    success, stdout, stderr = run_command("docker build -t queue-db-test .")
    print_test("Docker Image Built", success, stderr if not success else "Image built successfully")
    
    if not success:
        print("❌ Failed to build Docker image. Check Dockerfile and dependencies.")
        return
    
    # Test 3: Start the container
    print("\n3. Starting Queue-DB container...")
    success, stdout, stderr = run_command("docker run -d --name queue-db-test -e POSTGRES_DB=queue-db -e POSTGRES_USER=queue-admin -e POSTGRES_PASSWORD=queue-pwd -e USE_DEMO_DATA=True -p 5434:5432 queue-db-test")
    print_test("Container Started", success, stderr if not success else "Container started on port 5434")
    
    if not success:
        print("❌ Failed to start container. Check if port 5434 is available.")
        return
    
    # Test 4: Wait for database to be ready
    print("\n4. Waiting for database to be ready...")
    import time
    for i in range(30):
        success, stdout, stderr = run_command("docker exec queue-db-test pg_isready -U queue-admin -d queue-db")
        if success:
            print_test("Database Ready", True, f"Ready after {i+1} attempts")
            break
        time.sleep(2)
    else:
        print_test("Database Ready", False, "Database failed to become ready")
        return
    
    # Test 5: Test schema
    print("\n5. Testing database schema...")
    
    # Test investment queue table
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\dt investment_queue"')
    print_test("Investment Queue Table Exists", success, stderr if not success else "Table found")
    
    # Test withdrawal queue table
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\dt withdrawal_queue"')
    print_test("Withdrawal Queue Table Exists", success, stderr if not success else "Table found")
    
    # Test 6: Test data loading
    print("\n6. Testing data loading...")
    
    # Count investment queue entries
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT COUNT(*) FROM investment_queue;"')
    if success:
        count = stdout.strip().split('\n')[-2] if stdout else "0"
        print_test("Investment Data Loaded", True, f"Found {count} entries")
    else:
        print_test("Investment Data Loaded", False, stderr)
    
    # Count withdrawal queue entries
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT COUNT(*) FROM withdrawal_queue;"')
    if success:
        count = stdout.strip().split('\n')[-2] if stdout else "0"
        print_test("Withdrawal Data Loaded", True, f"Found {count} entries")
    else:
        print_test("Withdrawal Data Loaded", False, stderr)
    
    # Test 7: Test UUID consistency functions
    print("\n7. Testing UUID consistency functions...")
    
    # Test UUID generation
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT generate_queue_uuid();"')
    print_test("UUID Generation Function", success, stderr if not success else "Function works")
    
    # Test UUID validation
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT validate_uuid_consistency(\'550e8400-e29b-41d4-a716-446655440001\', \'INVESTMENT\');"')
    print_test("UUID Validation Function", success, stderr if not success else "Function works")
    
    # Test 8: Test constraints
    print("\n8. Testing constraints...")
    
    # Test invalid status constraint
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 100.0, 200.0, 300.0, \'550e8400-e29b-41d4-a716-446655440999\', \'INVALID_STATUS\');"')
    print_test("Status Constraint (should fail)", not success, "Constraint working" if not success else "Constraint failed")
    
    # Test 9: Test cross-table UUID uniqueness
    print("\n9. Testing cross-table UUID uniqueness...")
    
    # Insert same UUID in different tables (should fail)
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 50.0, 100.0, 150.0, \'550e8400-e29b-41d4-a716-446655440001\', \'PENDING\');"')
    print_test("Cross-Table UUID Constraint (should fail)", not success, "Constraint working" if not success else "Constraint failed")
    
    # Test 10: Cleanup
    print("\n10. Cleaning up...")
    success, stdout, stderr = run_command("docker stop queue-db-test")
    print_test("Container Stopped", success, stderr if not success else "Container stopped")
    
    success, stdout, stderr = run_command("docker rm queue-db-test")
    print_test("Container Removed", success, stderr if not success else "Container removed")
    
    print("\n🎉 Queue-DB Simple Test Suite Complete!")
    print("=" * 40)

if __name__ == "__main__":
    main()
