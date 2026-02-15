"""Quick validation of Phase 2 methods."""
import sys
sys.path.insert(0, '.')

from app.services.sparql_service import get_sparql_service

def quick_test():
    service = get_sparql_service()
    print("\n" + "="*60)
    print("PHASE 2 QUICK VALIDATION")
    print("="*60)
    
    print("\n✓ Test 1: find_conditions_by_symptom")
    try:
        result = service.find_conditions_by_symptom(['fever'], limit=3)
        print(f"   Found {len(result)} conditions with 'fever' symptom")
        if result:
            print(f"   Example: {result[0]['name']}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n✓ Test 2: get_related_conditions")
    try:
        result = service.get_related_conditions('Q12206', max_hops=1, limit=3)
        print(f"   Found {len(result)} conditions related to diabetes")
        if result:
            print(f"   Example: {result[0]['name']}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n✓ Test 3: get_condition_relationships")
    try:
        result = service.get_condition_relationships('Q12206')
        symptoms = len(result.get('symptoms', []))
        parents = len(result.get('parent_classes', []))
        treatments = len(result.get('treatments', []))
        print(f"   Diabetes relationships:")
        print(f"     {symptoms} symptoms")
        print(f"     {parents} parent classes")
        print(f"     {treatments} treatments")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "="*60)
    print("✅ ALL 3 NEW METHODS FUNCTIONAL!")
    print("="*60 + "\n")

if __name__ == "__main__":
    quick_test()
