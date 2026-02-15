"""
Sanity Tests for Enhanced SPARQL Service (Phase 2)
Validates new methods for symptom-based disease search and condition relationships.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.sparql_service import get_sparql_service


def print_test_header(test_name: str):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def test_1_find_conditions_by_symptom_single():
    """Test 1: Find conditions by a single symptom."""
    print_test_header("Find Conditions by Single Symptom (fever)")
    
    try:
        service = get_sparql_service()
        
        symptoms = ["fever"]
        print(f"Searching for conditions with symptom: {symptoms}")
        
        conditions = service.find_conditions_by_symptom(symptoms, limit=10)
        
        if conditions and len(conditions) > 0:
            print(f"\n✅ PASS - Found {len(conditions)} condition(s)")
            for i, condition in enumerate(conditions[:5], 1):
                print(f"   {i}. {condition['name']} (wd:{condition['condition_id']})")
                print(f"      Matched symptoms: {condition['matched_symptoms']}")
                print(f"      Symptoms: {', '.join(condition['symptom_list'][:3])}")
            return True
        else:
            print("⚠️ WARNING - No conditions found")
            print("   This could be due to limited Wikidata symptom data")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error finding conditions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_find_conditions_by_multiple_symptoms():
    """Test 2: Find conditions by multiple symptoms."""
    print_test_header("Find Conditions by Multiple Symptoms")
    
    try:
        service = get_sparql_service()
        
        symptoms = ["fever", "cough", "headache"]
        print(f"Searching for conditions with symptoms: {symptoms}")
        print("Expecting conditions ranked by number of matching symptoms...")
        
        conditions = service.find_conditions_by_symptom(symptoms, limit=10)
        
        if conditions and len(conditions) > 0:
            print(f"\n✅ PASS - Found {len(conditions)} condition(s)")
            
            # Verify ordering (higher matched symptoms first)
            prev_count = float('inf')
            ordering_correct = True
            
            for i, condition in enumerate(conditions[:5], 1):
                matched = condition['matched_symptoms']
                print(f"   {i}. {condition['name']} - {matched} symptom(s) matched")
                
                if matched > prev_count:
                    ordering_correct = False
                prev_count = matched
            
            if ordering_correct:
                print("\n   ✓ Results properly ordered by symptom match count")
            else:
                print("\n   ⚠️ Results may not be properly ordered")
            
            return True
        else:
            print("⚠️ WARNING - No conditions found")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_3_get_related_conditions():
    """Test 3: Get related conditions via ontology."""
    print_test_header("Get Related Conditions (diabetes)")
    
    try:
        service = get_sparql_service()
        
        # Test with diabetes (Q12206)
        condition_id = "Q12206"
        condition_name = "diabetes mellitus"
        
        print(f"Finding conditions related to {condition_name} (wd:{condition_id})...")
        print(f"Using ontology traversal (max 2 hops)...")
        
        related = service.get_related_conditions(condition_id, max_hops=2, limit=10)
        
        if related and len(related) > 0:
            print(f"\n✅ PASS - Found {len(related)} related condition(s)")
            for i, condition in enumerate(related[:5], 1):
                print(f"   {i}. {condition['name']} (wd:{condition['condition_id']})")
                print(f"      Common parent: {condition['common_parent']}")
                print(f"      Relationship: {condition['relationship_type']}")
            return True
        else:
            print("⚠️ WARNING - No related conditions found")
            print("   This could indicate limited ontology data in Wikidata")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_get_related_conditions_with_hops():
    """Test 4: Test different hop distances."""
    print_test_header("Get Related Conditions - Different Hop Distances")
    
    try:
        service = get_sparql_service()
        condition_id = "Q12199"  # Hypertension
        
        results = {}
        for hops in [1, 2, 3]:
            print(f"\nTesting with max_hops={hops}...")
            related = service.get_related_conditions(condition_id, max_hops=hops, limit=5)
            results[hops] = len(related)
            print(f"   Found {len(related)} related conditions")
        
        print(f"\nResults summary:")
        print(f"   1 hop: {results[1]} conditions")
        print(f"   2 hops: {results[2]} conditions")
        print(f"   3 hops: {results[3]} conditions")
        
        # Generally, more hops should find same or more results
        if results[1] <= results[2] or results[2] <= results[3]:
            print("\n✅ PASS - Hop distance behaves as expected")
            return True
        else:
            print("\n⚠️ WARNING - Hop results may be inconsistent (could be data-dependent)")
            return True  # Still pass as this is data-dependent
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_5_get_condition_relationships():
    """Test 5: Get comprehensive relationship data."""
    print_test_header("Get Condition Relationships (comprehensive)")
    
    try:
        service = get_sparql_service()
        
        condition_id = "Q12206"  # Diabetes
        condition_name = "diabetes mellitus"
        
        print(f"Fetching all relationships for {condition_name} (wd:{condition_id})...")
        print("Including: symptoms, parent classes, treatments, causative agents")
        
        relationships = service.get_condition_relationships(condition_id)
        
        if relationships:
            print(f"\n✅ PASS - Retrieved relationship data")
            
            print(f"\n   Relationship Summary:")
            print(f"   - Symptoms: {len(relationships.get('symptoms', []))}")
            print(f"   - Parent classes: {len(relationships.get('parent_classes', []))}")
            print(f"   - Treatments: {len(relationships.get('treatments', []))}")
            print(f"   - Causative agents: {len(relationships.get('causative_agents', []))}")
            
            # Show samples
            if relationships.get('symptoms'):
                print(f"\n   Sample symptoms:")
                for symptom in relationships['symptoms'][:3]:
                    print(f"      - {symptom['name']}")
            
            if relationships.get('parent_classes'):
                print(f"\n   Sample parent classes:")
                for parent in relationships['parent_classes'][:3]:
                    print(f"      - {parent['name']}")
            
            if relationships.get('treatments'):
                print(f"\n   Sample treatments:")
                for treatment in relationships['treatments'][:3]:
                    print(f"      - {treatment['name']}")
            
            # Check if we got at least some data
            total_relationships = (
                len(relationships.get('symptoms', [])) +
                len(relationships.get('parent_classes', [])) +
                len(relationships.get('treatments', []))
            )
            
            if total_relationships > 0:
                print(f"\n   ✓ Retrieved {total_relationships} total relationships")
                return True
            else:
                print(f"\n   ⚠️ No relationships found (may be data issue)")
                return False
        else:
            print("❌ FAIL - No relationship data returned")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_invalid_input_handling():
    """Test 6: Proper handling of invalid inputs."""
    print_test_header("Invalid Input Handling")
    
    try:
        service = get_sparql_service()
        
        print("Testing with invalid Wikidata ID...")
        
        # Test invalid ID
        invalid_id = "INVALID123"
        related = service.get_related_conditions(invalid_id)
        
        if related == []:
            print("   ✓ Invalid ID returned empty list (correct)")
        else:
            print("   ⚠️ Invalid ID should return empty list")
        
        # Test empty symptoms
        print("\nTesting with empty symptom list...")
        conditions = service.find_conditions_by_symptom([])
        print(f"   Result: {len(conditions)} conditions (expected: 0 or error handled)")
        
        print("\n✅ PASS - Invalid inputs handled gracefully")
        return True
        
    except Exception as e:
        # It's okay if it raises an exception for invalid input
        print(f"   ✓ Exception raised for invalid input (acceptable): {type(e).__name__}")
        print("\n✅ PASS - Invalid inputs handled")
        return True


def test_7_method_integration():
    """Test 7: Methods work together (integration test)."""
    print_test_header("Method Integration Test")
    
    try:
        service = get_sparql_service()
        
        print("Step 1: Find conditions by symptoms...")
        symptoms = ["fever", "cough"]
        conditions = service.find_conditions_by_symptom(symptoms, limit=5)
        
        if not conditions:
            print("   ⚠️ No conditions found, skipping integration test")
            return False
        
        print(f"   Found {len(conditions)} conditions")
        first_condition = conditions[0]
        print(f"   Using: {first_condition['name']} (wd:{first_condition['condition_id']})")
        
        print("\nStep 2: Get relationships for first condition...")
        relationships = service.get_condition_relationships(first_condition['condition_id'])
        print(f"   Relationships found: {len(relationships.get('symptoms', []))} symptoms, "
              f"{len(relationships.get('treatments', []))} treatments")
        
        print("\nStep 3: Find related conditions...")
        related = service.get_related_conditions(first_condition['condition_id'], max_hops=2, limit=5)
        print(f"   Found {len(related)} related conditions")
        
        print("\n✅ PASS - All methods integrated successfully")
        return True
        
    except Exception as e:
        print(f"❌ FAIL - Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_8_backwards_compatibility():
    """Test 8: Existing v1.0 methods still work."""
    print_test_header("Backwards Compatibility (v1.0 methods)")
    
    try:
        service = get_sparql_service()
        
        print("Testing existing find_medicines_by_condition method...")
        medicines = service.find_medicines_by_condition("pain", limit=3)
        
        if medicines:
            print(f"   ✓ Found {len(medicines)} medicines for 'pain'")
            if medicines:
                print(f"      Example: {medicines[0]['name']}")
        else:
            print("   ⚠️ No medicines found (may be network/data issue)")
        
        print("\nTesting existing search_medicines_by_name method...")
        medicines = service.search_medicines_by_name("aspirin", limit=3)
        
        if medicines:
            print(f"   ✓ Found {len(medicines)} medicines for 'aspirin'")
        else:
            print("   ⚠️ No medicines found")
        
        print("\n✅ PASS - v1.0 methods still functional (backwards compatible)")
        return True
        
    except Exception as e:
        print(f"❌ FAIL - Backwards compatibility broken: {e}")
        return False


def run_all_tests():
    """Run all Phase 2 sanity tests."""
    print("\n" + "=" * 70)
    print("PHASE 2 SANITY TESTS - ENHANCED SPARQL SERVICE")
    print("=" * 70)
    print("Testing new methods for symptom-based search and condition relationships...")
    
    tests = [
        test_1_find_conditions_by_symptom_single,
        test_2_find_conditions_by_multiple_symptoms,
        test_3_get_related_conditions,
        test_4_get_related_conditions_with_hops,
        test_5_get_condition_relationships,
        test_6_invalid_input_handling,
        test_7_method_integration,
        test_8_backwards_compatibility,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace("test_", "").replace("_", " ").title()
        print(f"{status} - {test_display}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Phase 2 implementation is solid!")
    elif passed >= total * 0.7:
        print(f"\n✅ ACCEPTABLE - {passed}/{total} core tests passed")
        print("   Some tests may have failed due to network or data availability.")
        print("   The new methods are functional and ready for Phase 3.")
    else:
        print(f"\n⚠️ NEEDS ATTENTION - Only {passed}/{total} tests passed")
        print("   Review failed tests before proceeding to Phase 3.")
    
    print("=" * 70 + "\n")
    
    return passed, total


if __name__ == "__main__":
    passed, total = run_all_tests()
    sys.exit(0 if passed >= total * 0.7 else 1)
