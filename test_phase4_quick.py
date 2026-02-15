"""
Phase 4 Validation Tests - V2 API Endpoints

Tests the three new similarity-based search endpoints:
1. POST /api/v2/search/symptom
2. POST /api/v2/search/disease
3. POST /api/v2/drugs/similar

Run: python test_phase4_quick.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test_result(test_name, passed, details=""):
    """Print test result"""
    status = "PASS" if passed else "FAIL"
    print(f"\n[{status}] {test_name}")
    if details:
        print(f"      {details}")


def test_v2_root():
    """Test V2 API root endpoint"""
    print_header("Test 1: V2 API Root Endpoint")
    
    try:
        response = client.get("/api/v2/")
        
        if response.status_code != 200:
            print_test_result("V2 Root", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["name", "version", "endpoints", "algorithm"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_test_result("V2 Root", False, f"Missing fields: {missing}")
            return False
        
        # Check endpoints
        endpoints = data.get("endpoints", {})
        required_endpoints = ["symptom_search", "disease_search", "drug_similarity"]
        missing_endpoints = [e for e in required_endpoints if e not in endpoints]
        
        if missing_endpoints:
            print_test_result("V2 Root", False, f"Missing endpoints: {missing_endpoints}")
            return False
        
        print_test_result("V2 Root", True, 
                         f"Version: {data['version']}, Algorithm: {data['algorithm']['type']}")
        print(f"      Endpoints: {list(endpoints.keys())}")
        return True
        
    except Exception as e:
        print_test_result("V2 Root", False, f"Error: {str(e)}")
        return False


def test_v2_health():
    """Test V2 health check"""
    print_header("Test 2: V2 Health Check")
    
    try:
        response = client.get("/api/v2/health")
        
        if response.status_code != 200:
            print_test_result("V2 Health", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("status") != "healthy":
            print_test_result("V2 Health", False, f"Status: {data.get('status')}")
            return False
        
        services = data.get("services", {})
        print_test_result("V2 Health", True, f"Services: {list(services.keys())}")
        return True
        
    except Exception as e:
        print_test_result("V2 Health", False, f"Error: {str(e)}")
        return False


def test_symptom_search():
    """Test symptom-based search endpoint"""
    print_header("Test 3: POST /api/v2/search/symptom")
    
    try:
        # Test request
        payload = {
            "symptoms": ["fever", "headache"],
            "top_k": 5,
            "min_similarity": 0.7
        }
        
        print(f"   Request: {payload}")
        
        response = client.post("/api/v2/search/symptom", json=payload)
        
        if response.status_code != 200:
            print_test_result("Symptom Search", False, 
                            f"Status: {response.status_code}, {response.text[:200]}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["success", "query_type", "recommendations", "total_found"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_test_result("Symptom Search", False, f"Missing fields: {missing}")
            return False
        
        if data["query_type"] != "symptom":
            print_test_result("Symptom Search", False, f"Wrong query_type: {data['query_type']}")
            return False
        
        recommendations = data["recommendations"]
        total = data["total_found"]
        
        print_test_result("Symptom Search", True, 
                         f"Found {total} drugs in {data.get('search_metadata', {}).get('execution_time_ms', 'N/A')}ms")
        
        if recommendations:
            drug = recommendations[0]
            print(f"      Example: {drug['drug_name']} (score: {drug['similarity_score']:.3f})")
            print(f"      Explanation: {drug['explanation'][:80]}...")
        
        return True
        
    except Exception as e:
        print_test_result("Symptom Search", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_disease_search():
    """Test disease-based search endpoint"""
    print_header("Test 4: POST /api/v2/search/disease")
    
    try:
        # Test request
        payload = {
            "disease_name": "Type 2 Diabetes",
            "top_k": 5,
            "min_similarity": 0.7
        }
        
        print(f"   Request: {payload}")
        
        response = client.post("/api/v2/search/disease", json=payload)
        
        if response.status_code != 200:
            print_test_result("Disease Search", False, 
                            f"Status: {response.status_code}, {response.text[:200]}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["success", "query_type", "recommendations", "total_found"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_test_result("Disease Search", False, f"Missing fields: {missing}")
            return False
        
        if data["query_type"] != "disease":
            print_test_result("Disease Search", False, f"Wrong query_type: {data['query_type']}")
            return False
        
        recommendations = data["recommendations"]
        total = data["total_found"]
        
        print_test_result("Disease Search", True, 
                         f"Found {total} drugs in {data.get('search_metadata', {}).get('execution_time_ms', 'N/A')}ms")
        
        if recommendations:
            drug = recommendations[0]
            print(f"      Example: {drug['drug_name']} (score: {drug['similarity_score']:.3f})")
            print(f"      Treats: {', '.join(drug['treats_conditions'][:3])}")
        
        return True
        
    except Exception as e:
        print_test_result("Disease Search", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_drug_similarity():
    """Test drug similarity endpoint"""
    print_header("Test 5: POST /api/v2/drugs/similar")
    
    try:
        # Test request
        payload = {
            "drug_name": "Aspirin",
            "drug_id": "Q18216",
            "top_k": 5,
            "min_similarity": 0.7
        }
        
        print(f"   Request: {payload}")
        
        response = client.post("/api/v2/drugs/similar", json=payload)
        
        if response.status_code != 200:
            print_test_result("Drug Similarity", False, 
                            f"Status: {response.status_code}, {response.text[:200]}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["success", "query_type", "recommendations", "total_found"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_test_result("Drug Similarity", False, f"Missing fields: {missing}")
            return False
        
        if data["query_type"] != "drug_similarity":
            print_test_result("Drug Similarity", False, f"Wrong query_type: {data['query_type']}")
            return False
        
        recommendations = data["recommendations"]
        total = data["total_found"]
        
        print_test_result("Drug Similarity", True, 
                         f"Found {total} similar drugs in {data.get('search_metadata', {}).get('execution_time_ms', 'N/A')}ms")
        
        if recommendations:
            drug = recommendations[0]
            print(f"      Example: {drug['drug_name']} (score: {drug['similarity_score']:.3f})")
            print(f"      Explanation: {drug['explanation'][:80]}...")
        
        return True
        
    except Exception as e:
        print_test_result("Drug Similarity", False, f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """Test request validation"""
    print_header("Test 6: Request Validation")
    
    try:
        # Test empty symptoms
        response = client.post("/api/v2/search/symptom", json={
            "symptoms": [],
            "top_k": 5,
            "min_similarity": 0.7
        })
        
        if response.status_code != 422:  # Validation error
            print_test_result("Validation (empty symptoms)", False, 
                            f"Expected 422, got {response.status_code}")
            return False
        
        # Test invalid similarity threshold
        response = client.post("/api/v2/search/symptom", json={
            "symptoms": ["fever"],
            "top_k": 5,
            "min_similarity": 1.5  # Invalid: > 1.0
        })
        
        if response.status_code != 422:
            print_test_result("Validation (invalid threshold)", False, 
                            f"Expected 422, got {response.status_code}")
            return False
        
        # Test invalid top_k
        response = client.post("/api/v2/search/disease", json={
            "disease_name": "Diabetes",
            "top_k": 100,  # Invalid: > 20
            "min_similarity": 0.7
        })
        
        if response.status_code != 422:
            print_test_result("Validation (invalid top_k)", False, 
                            f"Expected 422, got {response.status_code}")
            return False
        
        print_test_result("Validation", True, "All validation tests passed")
        return True
        
    except Exception as e:
        print_test_result("Validation", False, f"Error: {str(e)}")
        return False


def run_all_tests():
    """Run all Phase 4 tests"""
    print("\n" + "=" * 70)
    print("  PHASE 4 VALIDATION - V2 API ENDPOINTS")
    print("=" * 70)
    print("\n  Testing FastAPI endpoints with TestClient")
    print("  No server startup required - using ASGI app directly")
    
    tests = [
        ("V2 Root", test_v2_root),
        ("V2 Health", test_v2_health),
        ("Symptom Search", test_symptom_search),
        ("Disease Search", test_disease_search),
        ("Drug Similarity", test_drug_similarity),
        ("Validation", test_validation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name}: {str(e)}")
            results.append((name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\n  Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  Phase 4 API Endpoints: FULLY FUNCTIONAL")
    else:
        print(f"\n  Phase 4 API Endpoints: {total - passed} test(s) failed")
    
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
