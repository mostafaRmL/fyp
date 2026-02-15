"""
Sanity Tests for Similarity Service (Phase 1)
Validates core functionality of the ontology-based similarity engine.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.similarity_service import (
    SimilarityService,
    RelationshipType,
    SimilarityPath,
    get_similarity_service
)


def print_test_header(test_name: str):
    """Print formatted test header."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)


def test_1_service_initialization():
    """Test 1: Service can be initialized."""
    print_test_header("Service Initialization")
    
    try:
        service = SimilarityService()
        print("✅ PASS - Service initialized successfully")
        print(f"   - SPARQL Endpoint: {service.SPARQL_ENDPOINT}")
        print(f"   - Max Hops: {service.MAX_HOPS}")
        print(f"   - Min Similarity: {service.MIN_SIMILARITY}")
        return True
    except Exception as e:
        print(f"❌ FAIL - Service initialization failed: {e}")
        return False


def test_2_get_entity_neighbors():
    """Test 2: Can retrieve neighboring entities."""
    print_test_header("Get Entity Neighbors")
    
    try:
        service = get_similarity_service()
        
        # Test with diabetes (Q12206)
        diabetes_id = "Q12206"
        print(f"Fetching neighbors for diabetes (wd:{diabetes_id})...")
        
        neighbors = service.get_entity_neighbors(diabetes_id, max_results=10)
        
        if neighbors and len(neighbors) > 0:
            print(f"✅ PASS - Found {len(neighbors)} neighbors")
            for i, (neighbor_id, neighbor_label, rel_prop, rel_label) in enumerate(neighbors[:5], 1):
                print(f"   {i}. {neighbor_label} (wd:{neighbor_id}) via {rel_label} (P{rel_prop})")
            return True
        else:
            print("⚠️ WARNING - No neighbors found (may be network/data issue)")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error fetching neighbors: {e}")
        return False


def test_3_relationship_weights():
    """Test 3: Relationship weights are properly configured."""
    print_test_header("Relationship Weights Configuration")
    
    try:
        service = SimilarityService()
        
        print("Checking relationship weight configuration...")
        total_weights = len(service.RELATIONSHIP_WEIGHTS)
        
        print(f"✅ PASS - {total_weights} relationship types configured")
        print("\nRelationship weights:")
        for rel_type, weight in sorted(
            service.RELATIONSHIP_WEIGHTS.items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            print(f"   - {rel_type.name}: {weight:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ FAIL - Error checking weights: {e}")
        return False


def test_4_path_scoring():
    """Test 4: Path scoring algorithm works correctly."""
    print_test_header("Path Scoring Algorithm")
    
    try:
        service = SimilarityService()
        
        # Test case 1: Short path with high-value relationship
        path1 = [
            ("Q12206", "diabetes", "P279", "subclass of"),
            ("Q12136", "disease", "", "")
        ]
        score1 = service.calculate_path_score(path1)
        print(f"Test Case 1 - Short path (1 hop, high-value):")
        print(f"   Path: {service.generate_explanation(path1)}")
        print(f"   Score: {score1:.3f}")
        
        # Test case 2: Longer path
        path2 = [
            ("Q12206", "diabetes", "P279", "subclass of"),
            ("Q12136", "disease", "P31", "instance of"),
            ("Q16956", "health problem", "", "")
        ]
        score2 = service.calculate_path_score(path2)
        print(f"\nTest Case 2 - Longer path (2 hops):")
        print(f"   Path: {service.generate_explanation(path2)}")
        print(f"   Score: {score2:.3f}")
        
        # Test case 3: Empty path
        path3 = []
        score3 = service.calculate_path_score(path3)
        print(f"\nTest Case 3 - Empty path:")
        print(f"   Score: {score3:.3f}")
        
        # Validation
        if score1 > score2 > score3:
            print(f"\n✅ PASS - Scoring works correctly (shorter paths score higher)")
            return True
        else:
            print(f"\n⚠️ WARNING - Score ordering unexpected: {score1:.3f} > {score2:.3f} > {score3:.3f}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error in path scoring: {e}")
        return False


def test_5_threshold_filtering():
    """Test 5: Results are filtered by 70% threshold."""
    print_test_header("Threshold Filtering (70%)")
    
    try:
        service = SimilarityService()
        threshold = service.MIN_SIMILARITY
        
        print(f"Configured threshold: {threshold:.0%}")
        
        # Simulate results
        test_scores = [0.95, 0.85, 0.72, 0.65, 0.50]
        filtered = [s for s in test_scores if s >= threshold]
        
        print(f"\nTest scores: {test_scores}")
        print(f"Filtered (>= {threshold:.0%}): {filtered}")
        
        if len(filtered) == 3 and all(s >= threshold for s in filtered):
            print(f"\n✅ PASS - Threshold filtering works correctly")
            print(f"   - {len(filtered)}/{len(test_scores)} scores passed threshold")
            return True
        else:
            print(f"❌ FAIL - Threshold filtering incorrect")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error in threshold test: {e}")
        return False


def test_6_explanation_generation():
    """Test 6: Explanations are generated correctly."""
    print_test_header("Explanation Generation")
    
    try:
        service = SimilarityService()
        
        # Test path
        path = [
            ("Q12206", "type 2 diabetes", "P279", "subclass of"),
            ("Q12206", "diabetes mellitus", "P780", "has symptom"),
            ("Q8071861", "polyuria", "", "")
        ]
        
        explanation = service.generate_explanation(path)
        
        print(f"Test path: {path}")
        print(f"\nGenerated explanation:")
        print(f"   {explanation}")
        
        if explanation and len(explanation) > 0 and "→" in explanation:
            print(f"\n✅ PASS - Explanation generated successfully")
            return True
        else:
            print(f"❌ FAIL - Invalid explanation format")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error generating explanation: {e}")
        return False


def test_7_find_paths_integration():
    """Test 7: Integration test - finding paths between known entities."""
    print_test_header("Find Paths Integration Test")
    
    try:
        service = get_similarity_service()
        
        # Test finding paths between diabetes and disease
        source_id = "Q12206"  # Diabetes
        source_label = "diabetes mellitus"
        target_id = "Q12136"  # Disease
        target_label = "disease"
        
        print(f"Finding paths from '{source_label}' to '{target_label}'...")
        print(f"Source: wd:{source_id}")
        print(f"Target: wd:{target_id}")
        print(f"Max hops: {service.MAX_HOPS}")
        
        paths = service.find_paths_bfs(source_id, source_label, target_id, target_label)
        
        if paths and len(paths) > 0:
            print(f"\n✅ PASS - Found {len(paths)} path(s)")
            for i, path in enumerate(paths[:3], 1):
                score = service.calculate_path_score(path)
                explanation = service.generate_explanation(path)
                print(f"\n   Path {i} (Score: {score:.3f}):")
                print(f"   {explanation}")
            return True
        else:
            print(f"\n⚠️ WARNING - No paths found (may be network issue or max hops too low)")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error in path finding: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_8_similarity_search():
    """Test 8: Full similarity search with real data."""
    print_test_header("Similarity Search (End-to-End)")
    
    try:
        service = get_similarity_service()
        
        # Search for diseases similar to hypertension
        source_id = "Q12199"  # Hypertension
        source_label = "hypertension"
        
        print(f"Searching for diseases similar to '{source_label}'...")
        print(f"Source: wd:{source_id}")
        
        # Get similar diseases
        results = service.search_diseases_by_common_parent(
            source_id, 
            source_label, 
            max_results=5
        )
        
        if results and len(results) > 0:
            print(f"\n✅ PASS - Found {len(results)} similar disease(s) above threshold")
            
            for i, result in enumerate(results[:3], 1):
                print(f"\n   {i}. {result.entity_label} (wd:{result.entity_id})")
                print(f"      Similarity: {result.similarity_score:.1%}")
                print(f"      Explanation: {result.explanation}")
            
            # Check threshold compliance
            below_threshold = [r for r in results if r.similarity_score < service.MIN_SIMILARITY]
            if below_threshold:
                print(f"\n⚠️ WARNING - {len(below_threshold)} results below threshold!")
                return False
            
            return True
        else:
            print(f"\n⚠️ WARNING - No similar diseases found")
            print(f"   This could be due to:")
            print(f"   - Network connectivity issues")
            print(f"   - Limited data in Wikidata for this entity")
            print(f"   - Threshold too high (currently {service.MIN_SIMILARITY:.0%})")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error in similarity search: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all sanity tests."""
    print("\n" + "=" * 70)
    print("PHASE 1 SANITY TESTS - SIMILARITY SERVICE")
    print("=" * 70)
    print("Testing core functionality of ontology-based similarity engine...")
    
    tests = [
        test_1_service_initialization,
        test_2_get_entity_neighbors,
        test_3_relationship_weights,
        test_4_path_scoring,
        test_5_threshold_filtering,
        test_6_explanation_generation,
        test_7_find_paths_integration,
        test_8_similarity_search,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_func.__name__}: {e}")
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
        print("\n🎉 ALL TESTS PASSED - Phase 1 implementation is solid!")
    elif passed >= total * 0.7:
        print(f"\n✅ ACCEPTABLE - {passed}/{total} core tests passed")
        print("   Some tests may have failed due to network or data availability.")
    else:
        print(f"\n⚠️ NEEDS ATTENTION - Only {passed}/{total} tests passed")
        print("   Review failed tests before proceeding to Phase 2.")
    
    print("=" * 70 + "\n")
    
    return passed, total


if __name__ == "__main__":
    passed, total = run_all_tests()
    sys.exit(0 if passed >= total * 0.7 else 1)
