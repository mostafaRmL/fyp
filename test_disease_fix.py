"""
Test disease search without ID
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

# Test 1: Disease without ID
print("="*60)
print("Testing: Disease search WITHOUT Wikidata ID")
print("="*60)

payload = {
    "disease_name": "diabetes",
    "top_k": 3,
    "min_similarity": 0.5
}

print(f"Request: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/v2/search/disease",
        json=payload,
        timeout=30
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Total Found: {data.get('total_found')}")
        print(f"💬 Message: {data.get('message')}")
        
        if data.get('recommendations'):
            print(f"\n🔹 Drugs Found:")
            for i, drug in enumerate(data['recommendations'], 1):
                print(f"   {i}. {drug['drug_name']} ({drug['drug_id']})")
                print(f"      Score: {drug['similarity_score']}")
        else:
            print("\n❌ No recommendations returned")
            print(f"   Metadata: {data.get('search_metadata')}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

# Test 2: Disease WITH ID
print("\n" + "="*60)
print("Testing: Disease search WITH Wikidata ID")
print("="*60)

payload2 = {
    "disease_name": "diabetes",
    "disease_id": "Q3025883",
    "top_k": 3,
    "min_similarity": 0.5
}

print(f"Request: {json.dumps(payload2, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/v2/search/disease",
        json=payload2,
        timeout=30
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Total Found: {data.get('total_found')}")
        
        if data.get('recommendations'):
            print(f"\n🔹 Drugs Found:")
            for i, drug in enumerate(data['recommendations'], 1):
                print(f"   {i}. {drug['drug_name']} ({drug['drug_id']})")
                print(f"      Score: {drug['similarity_score']}")
                
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)
