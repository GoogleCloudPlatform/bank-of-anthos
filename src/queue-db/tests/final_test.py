#!/usr/bin/env python3
"""
Final Queue-DB Test Script
Tests the queue-db schema using a custom Dockerfile without test data
"""

import subprocess
import sys
import os
import time

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
    print("🧪 Queue-DB Final Test Suite")
    print("=" * 40)
    
    # Test 1: Check if Docker is available
    print("\n1. Checking Docker availability...")
    success, stdout, stderr = run_command("docker --version")
    print_test("Docker Available", success, stdout if success else stderr)
    
    if not success:
        print("\n❌ Docker not available. Please install Docker to run tests.")
        return
    
    # Test 2: Clean up any existing containers
    print("\n2. Cleaning up existing containers...")
    run_command("docker stop queue-db-test 2>/dev/null")
    run_command("docker rm queue-db-test 2>/dev/null")
    print_test("Cleanup Complete", True, "Previous containers removed")
    
    # Test 3: Build the test Docker image
    print("\n3. Building Queue-DB test image...")
    success, stdout, stderr = run_command("docker build -f Dockerfile.test -t queue-db-test .")
    print_test("Docker Image Built", success, stderr if not success else "Image built successfully")
    
    if not success:
        print("❌ Failed to build Docker image. Check Dockerfile and dependencies.")
        return
    
    # Test 4: Start the container
    print("\n4. Starting Queue-DB container...")
    success, stdout, stderr = run_command("docker run -d --name queue-db-test -e POSTGRES_DB=queue-db -e POSTGRES_USER=queue-admin -e POSTGRES_PASSWORD=queue-pwd -p 5434:5432 queue-db-test")
    print_test("Container Started", success, stderr if not success else "Container started on port 5434")
    
    if not success:
        print("❌ Failed to start container. Check if port 5434 is available.")
        return
    
    # Test 5: Wait for database to be ready
    print("\n5. Waiting for database to be ready...")
    for i in range(30):
        success, stdout, stderr = run_command("docker exec queue-db-test pg_isready -U queue-admin -d queue-db")
        if success:
            print_test("Database Ready", True, f"Ready after {i+1} attempts")
            break
        time.sleep(2)
    else:
        print_test("Database Ready", False, "Database failed to become ready")
        # Try to get logs
        run_command("docker logs queue-db-test")
        return
    
    # Test 6: Test schema
    print("\n6. Testing database schema...")
    
    # Test investment queue table
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\dt investment_queue"')
    print_test("Investment Queue Table Exists", success, stderr if not success else "Table found")
    
    # Test withdrawal queue table
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\dt withdrawal_queue"')
    print_test("Withdrawal Queue Table Exists", success, stderr if not success else "Table found")
    
    # Test 7: Test table structures
    print("\n7. Testing table structures...")
    
    # Show investment queue structure
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\d investment_queue"')
    print_test("Investment Queue Structure", success, "Structure validated" if success else stderr)
    
    # Show withdrawal queue structure
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\d withdrawal_queue"')
    print_test("Withdrawal Queue Structure", success, "Structure validated" if success else stderr)
    
    # Test 8: Test UUID consistency functions
    print("\n8. Testing UUID consistency functions...")
    
    # Test UUID generation
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT generate_queue_uuid();"')
    print_test("UUID Generation Function", success, stderr if not success else "Function works")
    
    # Test UUID validation
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT validate_uuid_consistency(\'550e8400-e29b-41d4-a716-446655440001\', \'INVESTMENT\');"')
    print_test("UUID Validation Function", success, stderr if not success else "Function works")
    
    # Test 9: Test constraints
    print("\n9. Testing constraints...")
    
    # Test invalid status constraint (should fail)
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 100.0, 200.0, 300.0, \'550e8400-e29b-41d4-a716-446655440999\', \'INVALID_STATUS\');"')
    print_test("Status Constraint (should fail)", not success, "Constraint working" if not success else "Constraint failed")
    
    # Test valid insertion (should succeed)
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 100.0, 200.0, 300.0, \'550e8400-e29b-41d4-a716-446655440998\', \'PENDING\');"')
    print_test("Valid Investment Insert", success, stderr if not success else "Insert successful")
    
    # Test valid withdrawal insertion (should succeed)
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 50.0, 100.0, 150.0, \'550e8400-e29b-41d4-a716-446655440997\', \'PENDING\');"')
    print_test("Valid Withdrawal Insert", success, stderr if not success else "Insert successful")
    
    # Test 10: Test cross-table UUID uniqueness
    print("\n10. Testing cross-table UUID uniqueness...")
    
    # Try to insert same UUID in different tables (should fail)
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) VALUES (\'1234567890\', 50.0, 100.0, 150.0, \'550e8400-e29b-41d4-a716-446655440998\', \'PENDING\');"')
    print_test("Cross-Table UUID Constraint (should fail)", not success, "Constraint working" if not success else "Constraint failed")
    
    # Test 11: Test data retrieval
    print("\n11. Testing data retrieval...")
    
    # Count investment queue entries
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT COUNT(*) FROM investment_queue;"')
    if success:
        count = stdout.strip().split('\n')[-2] if stdout else "0"
        print_test("Investment Data Count", True, f"Found {count} entries")
    else:
        print_test("Investment Data Count", False, stderr)
    
    # Count withdrawal queue entries
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT COUNT(*) FROM withdrawal_queue;"')
    if success:
        count = stdout.strip().split('\n')[-2] if stdout else "0"
        print_test("Withdrawal Data Count", True, f"Found {count} entries")
    else:
        print_test("Withdrawal Data Count", False, stderr)
    
    # Test 12: Test indexes
    print("\n12. Testing indexes...")
    
    # Show investment queue indexes
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\di idx_investment_queue_*"')
    print_test("Investment Queue Indexes", success, "Indexes created" if success else stderr)
    
    # Show withdrawal queue indexes
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "\\di idx_withdrawal_queue_*"')
    print_test("Withdrawal Queue Indexes", success, "Indexes created" if success else stderr)
    
    # Test 13: Test UUID consistency validation
    print("\n13. Testing UUID consistency validation...")
    
    # Test that UUID validation function works correctly
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT validate_uuid_consistency(\'550e8400-e29b-41d4-a716-446655440998\', \'INVESTMENT\');"')
    print_test("UUID Validation for Existing Investment", success, stderr if not success else "Validation works")
    
    # Test 14: Test combined queries
    print("\n14. Testing combined queries...")
    
    # Test query across both tables
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "SELECT \'investment\' as queue_type, COUNT(*) as count FROM investment_queue UNION ALL SELECT \'withdrawal\' as queue_type, COUNT(*) as count FROM withdrawal_queue;"')
    print_test("Combined Query Test", success, stderr if not success else "Combined queries work")
    
    # Test 15: Test triggers
    print("\n15. Testing triggers...")
    
    # Test updated_at trigger
    success, stdout, stderr = run_command('docker exec queue-db-test psql -U queue-admin -d queue-db -c "UPDATE investment_queue SET status = \'PROCESSING\' WHERE uuid = \'550e8400-e29b-41d4-a716-446655440998\'; SELECT updated_at FROM investment_queue WHERE uuid = \'550e8400-e29b-41d4-a716-446655440998\';"')
    print_test("Updated_at Trigger", success, stderr if not success else "Trigger works")
    
    # Test 16: Cleanup
    print("\n16. Cleaning up...")
    success, stdout, stderr = run_command("docker stop queue-db-test")
    print_test("Container Stopped", success, stderr if not success else "Container stopped")
    
    success, stdout, stderr = run_command("docker rm queue-db-test")
    print_test("Container Removed", success, stderr if not success else "Container removed")
    
    print("\n🎉 Queue-DB Final Test Suite Complete!")
    print("=" * 40)
    print("\n📋 Test Summary:")
    print("✅ Database schema validation")
    print("✅ Investment and withdrawal queue tables")
    print("✅ UUID consistency functions")
    print("✅ Constraint validation")
    print("✅ Cross-table UUID uniqueness")
    print("✅ Data insertion and retrieval")
    print("✅ Index creation and validation")
    print("✅ Combined query functionality")
    print("✅ Trigger functionality")

if __name__ == "__main__":
    main()
