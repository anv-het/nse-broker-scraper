#!/usr/bin/env python3
"""
API Testing Script for NSE Broker Auth Person and Branch Data
============================================================
Simple test script to verify the new API endpoints are working correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://192.168.119.183:8758/api/v1"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Test data - Updated with actual broker data from database
SAMPLE_MEMBER_CODE = "14300"  # 5PAISA CAPITAL LIMITED
SAMPLE_MEM_ID = "2556"       # 5PAISA CAPITAL LIMITED mem_id
SAMPLE_SEARCH_QUERY = "5PAISA"  # Search for 5PAISA
SAMPLE_CITY = "MUMBAI"       # Multiple offices in Mumbai

def test_endpoint(endpoint: str, description: str) -> bool:
    """
    Test a single API endpoint.
    
    Args:
        endpoint (str): API endpoint path
        description (str): Description for logging
        
    Returns:
        bool: True if test passed, False otherwise
    """
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🧪 Testing: {description}")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Test PASSED")
                if 'data' in data:
                    if isinstance(data['data'], list):
                        print(f"📈 Records returned: {len(data['data'])}")
                    elif isinstance(data['data'], dict):
                        print("📈 Single record returned")
                if 'message' in data:
                    print(f"💬 Message: {data['message']}")
                return True
            else:
                print(f"❌ Test FAILED: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Test FAILED: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"💬 Error: {error_data.get('error', 'No error message')}")
            except:
                print(f"💬 Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test FAILED: Network error - {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Test FAILED: Invalid JSON response - {e}")
        return False
    except Exception as e:
        print(f"❌ Test FAILED: Unexpected error - {e}")
        return False

def run_auth_person_tests() -> int:
    """
    Run all auth person API tests.
    
    Returns:
        int: Number of passed tests
    """
    print("\n" + "="*80)
    print("🔐 TESTING AUTH PERSON ENDPOINTS")
    print("="*80)
    
    tests = [
        (f"/brokers/{SAMPLE_MEMBER_CODE}/auth-persons", f"Get Auth Person by Member Code ({SAMPLE_MEMBER_CODE})"),
        (f"/brokers/mem-id/{SAMPLE_MEM_ID}/auth-persons", f"Get Auth Person by Mem ID ({SAMPLE_MEM_ID})"),
        ("/auth-persons?page=1&limit=10", "Get All Auth Persons (Paginated)"),
        (f"/auth-persons/search?q={SAMPLE_SEARCH_QUERY}&limit=5", f"Search Auth Persons ('{SAMPLE_SEARCH_QUERY}')"),
        ("/auth-persons/statistics", "Get Auth Person Statistics"),
    ]
    
    passed = 0
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            passed += 1
    
    return passed

def run_branch_tests() -> int:
    """
    Run all branch office API tests.
    
    Returns:
        int: Number of passed tests
    """
    print("\n" + "="*80)
    print("🏢 TESTING BRANCH OFFICE ENDPOINTS")
    print("="*80)
    
    tests = [
        (f"/brokers/{SAMPLE_MEMBER_CODE}/branches", f"Get Branches by Member Code ({SAMPLE_MEMBER_CODE})"),
        (f"/brokers/mem-id/{SAMPLE_MEM_ID}/branches", f"Get Branches by Mem ID ({SAMPLE_MEM_ID})"),
        ("/branches?page=1&limit=10", "Get All Branches (Paginated)"),
        (f"/branches/search?q={SAMPLE_SEARCH_QUERY}&limit=5", f"Search Branches ('{SAMPLE_SEARCH_QUERY}')"),
        (f"/branches/city/{SAMPLE_CITY}?limit=5", f"Get Branches by City ('{SAMPLE_CITY}')"),
        ("/branches/statistics", "Get Branch Statistics"),
    ]
    
    passed = 0
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            passed += 1
    
    return passed

def run_health_check() -> bool:
    """
    Run health check test.
    
    Returns:
        bool: True if health check passed
    """
    print("\n" + "="*80)
    print("💚 TESTING HEALTH CHECK ENDPOINT")
    print("="*80)
    
    return test_endpoint("/health", "API Health Check")

def main():
    """Main test runner."""
    print("🚀 NSE Broker API Testing Suite")
    print("🎯 Testing Auth Person and Branch Office APIs")
    print("📅 " + "="*60)
    
    # Test health check first
    health_ok = run_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed! API server may be down.")
        print("🔧 Please ensure the backend server is running on http://192.168.119.183:8758")
        sys.exit(1)
    
    # Run auth person tests
    auth_passed = run_auth_person_tests()
    
    # Run branch tests
    branch_passed = run_branch_tests()
    
    # Summary
    total_tests = 11  # 5 auth + 6 branch
    total_passed = auth_passed + branch_passed
    
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Health Check: {'PASSED' if health_ok else 'FAILED'}")
    print(f"🔐 Auth Person APIs: {auth_passed}/5 passed")
    print(f"🏢 Branch Office APIs: {branch_passed}/6 passed")
    print(f"📈 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests PASSED! APIs are working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - total_passed} tests FAILED. Check the logs above for details.")
        print("🔧 Common issues:")
        print("   - Ensure MongoDB is running and connected")
        print("   - Check if auth person and branch data exists in database")
        print("   - Verify sample member codes exist in collections")
        sys.exit(1)

if __name__ == "__main__":
    main()
