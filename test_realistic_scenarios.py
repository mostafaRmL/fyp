"""
Additional workflow tests with realistic scenarios
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_multiple_symptoms():
    """Test with multiple symptoms like a real user"""
    print("\n" + "="*60)
    print("Test: Multiple Symptoms (fever, headache, cough)")
    print("="*60)
    
    payload = {
        "symptoms": ["fever", "headache", "cough"],
        "top_k": 5,
        "min_similarity": 0.6
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v2/search/symptom",
            json=payload,
            timeout=120
        )
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️ Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Results: {data.get('total_found')} drugs")
            
            for i, rec in enumerate(data.get('recommendations', [])[:3], 1):
                print(f"\n{i}. {rec.get('drug_name')} ({rec.get('drug_id')})")
                print(f"   Score: {rec.get('similarity_score')}")
                print(f"   Treats: {', '.join(rec.get('treats_conditions', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_common_diseases():
    """Test common diseases"""
    diseases = [
        {"name": "Type 2 Diabetes", "id": "Q3025883"},
        {"name": "Hypertension", "id": "Q41861"},
        {"name": "Asthma", "id": "Q35869"}
    ]
    
    results = []
    
    for disease in diseases:
        print("\n" + "="*60)
        print(f"Test: {disease['name']} ({disease['id']})")
        print("="*60)
        
        payload = {
            "disease_name": disease["name"],
            "disease_id": disease["id"],
            "top_k": 3,
            "min_similarity": 0.5
        }
        
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v2/search/disease",
                json=payload,
                timeout=60
            )
            elapsed = time.time() - start
            
            print(f"✅ Status: {response.status_code}")
            print(f"⏱️ Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                found = data.get('total_found', 0)
                print(f"📊 Results: {found} drugs")
                
                if found > 0:
                    rec = data['recommendations'][0]
                    print(f"   Top Drug: {rec.get('drug_name')}")
                
                results.append(True)
            else:
                results.append(False)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Extended Workflow Testing")
    print("="*60)
    
    test1 = test_multiple_symptoms()
    test2 = test_common_diseases()
    
    print("\n" + "="*60)
    print("Final Results")
    print("="*60)
    print(f"Multiple Symptoms: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Common Diseases: {'✅ PASS' if test2 else '❌ FAIL'}")
    print("="*60)
