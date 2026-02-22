"""
Quick test script for V2 API endpoints
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint...")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/api/v2/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_symptom_search():
    """Test symptom search with simple input"""
    print("\n" + "="*60)
    print("Testing Symptom Search...")
    print("="*60)
    
    payload = {
        "symptoms": ["fever"],
        "top_k": 2,
        "min_similarity": 0.5
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("Sending request (this may take 30-60 seconds)...")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v2/search/symptom",
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        elapsed = time.time() - start
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time taken: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess: {data.get('success')}")
            print(f"Total Found: {data.get('total_found')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('recommendations'):
                print(f"\nFirst Recommendation:")
                rec = data['recommendations'][0]
                print(f"  Drug: {rec.get('drug_name')} ({rec.get('drug_id')})")
                print(f"  Score: {rec.get('similarity_score')}")
                print(f"  Explanation: {rec.get('explanation', 'No explanation')[:100]}...")
            else:
                print("\nNo recommendations returned!")
        else:
            print(f"Error Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.Timeout:
        print("\nERROR: Request timed out after 120 seconds!")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

def test_disease_search():
    """Test disease search"""
    print("\n" + "="*60)
    print("Testing Disease Search...")
    print("="*60)
    
    payload = {
        "disease_name": "diabetes",
        "disease_id": "Q3025883",  # Type 2 Diabetes
        "top_k": 2,
        "min_similarity": 0.5
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("Sending request (this may take 30-60 seconds)...")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v2/search/disease",
            json=payload,
            timeout=120
        )
        elapsed = time.time() - start
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time taken: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess: {data.get('success')}")
            print(f"Total Found: {data.get('total_found')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('recommendations'):
                print(f"\nFirst Recommendation:")
                rec = data['recommendations'][0]
                print(f"  Drug: {rec.get('drug_name')} ({rec.get('drug_id')})")
                print(f"  Score: {rec.get('similarity_score')}")
            else:
                print("\nNo recommendations returned!")
        else:
            print(f"Error Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.Timeout:
        print("\nERROR: Request timed out after 120 seconds!")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MedSearch AI - V2 API Testing")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("\n❌ Health check failed! Server may not be running.")
        exit(1)
    
    print("\n✅ Health check passed!")
    
    # Test symptom search
    symptom_ok = test_symptom_search()
    
    # Test disease search
    disease_ok = test_disease_search()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Health Check: ✅ PASS")
    print(f"Symptom Search: {'✅ PASS' if symptom_ok else '❌ FAIL'}")
    print(f"Disease Search: {'✅ PASS' if disease_ok else '❌ FAIL'}")
    print("="*60)
