"""
Diagnostic script to check SPARQL service responses
"""
from app.services.sparql_service import get_sparql_service
from app.utils.logger import LoggerSetup

logger = LoggerSetup.get_logger(__name__)

def test_sparql_queries():
    """Test SPARQL queries to see what's being returned"""
    sparql = get_sparql_service()
    
    print("\n" + "="*60)
    print("SPARQL Service Diagnostic")
    print("="*60)
    
    # Test 1: Find conditions by symptom
    print("\nTest 1: Find conditions for 'fever'")
    print("-" * 60)
    conditions = sparql.find_conditions_by_symptom(["fever"], limit=5)
    print(f"Found {len(conditions)} conditions")
    for i, cond in enumerate(conditions[:3], 1):
        print(f"  {i}. {cond.get('name')} ({cond.get('condition_id')})")
        print(f"     Matched symptoms: {cond.get('matched_symptoms')}")
    
    if not conditions:
        print("  ❌ NO CONDITIONS FOUND - This explains why symptom search returns 0 results!")
    
    # Test 2: Find medicines by condition
    print("\nTest 2: Find medicines for 'diabetes'")
    print("-" * 60)
    drugs = sparql.find_medicines_by_condition("diabetes", limit=5)
    print(f"Found {len(drugs)} drugs")
    for i, drug in enumerate(drugs[:3], 1):
        print(f"  {i}. {drug.get('name')} ({drug.get('drug_id')})")
    
    if not drugs:
        print("  ❌ NO DRUGS FOUND")
    
    # Test 3: Get medicine details for a known drug
    print("\nTest 3: Get details for Metformin (Q19484)")
    print("-" * 60)
    details = sparql.get_medicine_details("Q19484")
    if details:
        print(f"  Drug Name: {details.get('name')}")
        print(f"  Formula: {details.get('chemical_formula')}")
        print(f"  Conditions: {len(details.get('medical_conditions', []))} found")
        for cond in details.get('medical_conditions', [])[:3]:
            print(f"    - {cond}")
    else:
        print("  ❌ NO DETAILS FOUND")
    
    # Test 4: Find related conditions for diabetes
    print("\nTest 4: Find related conditions for diabetes (Q3025883)")
    print("-" * 60)
    related = sparql.get_related_conditions("Q3025883", max_hops=2, limit=5)
    print(f"Found {len(related)} related conditions")
    for i, rel in enumerate(related[:3], 1):
        print(f"  {i}. {rel.get('name')} ({rel.get('condition_id')})")
    
    if not related:
        print("  ❌ NO RELATED CONDITIONS FOUND - This explains why disease search hangs!")
    
    print("\n" + "="*60)
    print("Diagnostic Summary")
    print("="*60)
    
    has_conditions = len(conditions) > 0
    has_drugs = len(drugs) > 0
    has_details = details is not None
    has_related = len(related) > 0
    
    print(f"Conditions by symptom: {'✅ OK' if has_conditions else '❌ FAIL'}")
    print(f"Drugs by condition: {'✅ OK' if has_drugs else '❌ FAIL'}")
    print(f"Medicine details: {'✅ OK' if has_details else '❌ FAIL'}")
    print(f"Related conditions: {'✅ OK' if has_related else '❌ FAIL'}")
    
    if not has_conditions:
        print("\n⚠️  WARNING: No conditions found for symptoms!")
        print("   This means SPARQL queries to Wikidata are not returning results.")
        print("   Possible causes:")
        print("   - Wikidata structure has changed")
        print("   - SPARQL endpoint is slow/timing out")
        print("   - Query syntax needs updating")
    
    if not has_related:
        print("\n⚠️  WARNING: No related conditions found!")
        print("   This could cause disease search to hang waiting for results.")
    
    print("="*60)

if __name__ == "__main__":
    try:
        test_sparql_queries()
    except Exception as e:
        print(f"\n❌ ERROR during diagnostic: {e}")
        import traceback
        traceback.print_exc()
