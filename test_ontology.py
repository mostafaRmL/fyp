"""
Test SPARQL queries for ontology-based similarity algorithm.
Verifies Wikidata has the necessary data for v2.0 implementation.
"""

import requests
import json
from typing import Dict, List

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

def query_wikidata(sparql_query: str) -> Dict:
    """Execute SPARQL query against Wikidata."""
    headers = {
        "User-Agent": "Medical-Assistant-FYP/2.0 (Educational Project)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(
            SPARQL_ENDPOINT,
            params={"query": sparql_query, "format": "json"},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return {}


def test_disease_hierarchy():
    """Test 1: Can we traverse disease subclass hierarchies?"""
    print("\n" + "="*70)
    print("TEST 1: Disease Hierarchy & Subclass Relationships")
    print("="*70)
    
    query = """
    SELECT ?disease ?diseaseLabel ?parent ?parentLabel WHERE {
      # Get diabetes and its parent classes
      ?disease wdt:P31 wd:Q12136.  # Instance of disease
      ?disease rdfs:label "diabetes mellitus"@en.
      ?disease wdt:P279* ?parent.  # Subclass of (with transitive closure)
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 10
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} hierarchy relationships")
        for item in bindings[:5]:
            disease = item.get("diseaseLabel", {}).get("value", "Unknown")
            parent = item.get("parentLabel", {}).get("value", "Unknown")
            print(f"  - {disease} → {parent}")
    else:
        print("❌ No hierarchy data found")
    
    return len(bindings) if result and "results" in result else 0


def test_disease_symptom_relationships():
    """Test 2: Can we find symptoms for diseases?"""
    print("\n" + "="*70)
    print("TEST 2: Disease-Symptom Relationships")
    print("="*70)
    
    query = """
    SELECT ?disease ?diseaseLabel ?symptom ?symptomLabel WHERE {
      # Find diseases and their symptoms
      VALUES ?diseaseType { wd:Q12136 wd:Q389735 }  # Disease or cardiovascular disease
      ?disease wdt:P31/wdt:P279* ?diseaseType.
      ?disease wdt:P780 ?symptom.  # Has symptom property
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 20
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} disease-symptom relationships")
        for item in bindings[:5]:
            disease = item.get("diseaseLabel", {}).get("value", "Unknown")
            symptom = item.get("symptomLabel", {}).get("value", "Unknown")
            print(f"  - {disease} has symptom: {symptom}")
    else:
        print("❌ No symptom data found")
    
    return len(bindings) if result and "results" in result else 0


def test_drug_disease_relationships():
    """Test 3: Can we find which drugs treat which diseases?"""
    print("\n" + "="*70)
    print("TEST 3: Drug-Disease Relationships (treats)")
    print("="*70)
    
    query = """
    SELECT ?drug ?drugLabel ?condition ?conditionLabel WHERE {
      # Find drugs that treat diseases
      ?drug wdt:P31/wdt:P279* wd:Q12140.  # Instance of medication
      ?drug wdt:P2175 ?condition.  # Medical condition treated
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 20
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} drug-disease relationships")
        for item in bindings[:5]:
            drug = item.get("drugLabel", {}).get("value", "Unknown")
            condition = item.get("conditionLabel", {}).get("value", "Unknown")
            print(f"  - {drug} treats: {condition}")
    else:
        print("❌ No drug-disease data found")
    
    return len(bindings) if result and "results" in result else 0


def test_drug_properties():
    """Test 4: Can we find drug properties for similarity?"""
    print("\n" + "="*70)
    print("TEST 4: Drug Properties (active ingredients, drug class)")
    print("="*70)
    
    query = """
    SELECT ?drug ?drugLabel ?ingredient ?ingredientLabel ?drugClass ?drugClassLabel WHERE {
      # Find drug properties
      VALUES ?drug { wd:Q18216 wd:Q27107351 }  # Aspirin, Metformin
      OPTIONAL { ?drug wdt:P3781 ?ingredient. }  # Active ingredient
      OPTIONAL { ?drug wdt:P279 ?drugClass. }  # Subclass of (drug class)
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} drug property relationships")
        for item in bindings[:5]:
            drug = item.get("drugLabel", {}).get("value", "Unknown")
            ingredient = item.get("ingredientLabel", {}).get("value", "N/A")
            drugClass = item.get("drugClassLabel", {}).get("value", "N/A")
            print(f"  - {drug}")
            if ingredient != "N/A":
                print(f"    Ingredient: {ingredient}")
            if drugClass != "N/A":
                print(f"    Class: {drugClass}")
    else:
        print("❌ No drug property data found")
    
    return len(bindings) if result and "results" in result else 0


def test_multi_hop_paths():
    """Test 5: Can we traverse multi-hop paths between diseases?"""
    print("\n" + "="*70)
    print("TEST 5: Multi-Hop Paths Between Related Diseases")
    print("="*70)
    
    query = """
    SELECT ?disease1 ?disease1Label ?disease2 ?disease2Label ?commonParent ?commonParentLabel WHERE {
      # Find diseases that share a common parent class
      VALUES ?disease1 { wd:Q12199 wd:Q3025883 }  # Hypertension, Coronary artery disease
      ?disease1 wdt:P279 ?commonParent.
      ?disease2 wdt:P279 ?commonParent.
      FILTER(?disease1 != ?disease2)
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT 10
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} multi-hop paths")
        for item in bindings[:5]:
            disease1 = item.get("disease1Label", {}).get("value", "Unknown")
            disease2 = item.get("disease2Label", {}).get("value", "Unknown")
            common = item.get("commonParentLabel", {}).get("value", "Unknown")
            print(f"  - {disease1} ← {common} → {disease2}")
    else:
        print("❌ No multi-hop path data found")
    
    return len(bindings) if result and "results" in result else 0


def test_symptom_to_disease_search():
    """Test 6: Can we find diseases from symptoms?"""
    print("\n" + "="*70)
    print("TEST 6: Symptom → Disease Search (for UI Mode 1)")
    print("="*70)
    
    query = """
    SELECT ?disease ?diseaseLabel (COUNT(?symptom) as ?symptomCount) WHERE {
      # Find diseases that have fever or headache as symptoms
      VALUES ?symptomName { "fever"@en "headache"@en "cough"@en }
      ?symptom rdfs:label ?symptomName.
      ?disease wdt:P31/wdt:P279* wd:Q12136.  # Instance of disease
      ?disease wdt:P780 ?symptom.
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    GROUP BY ?disease ?diseaseLabel
    ORDER BY DESC(?symptomCount)
    LIMIT 10
    """
    
    result = query_wikidata(query)
    if result and "results" in result:
        bindings = result["results"]["bindings"]
        print(f"\n✅ Found {len(bindings)} diseases matching symptoms")
        for item in bindings[:5]:
            disease = item.get("diseaseLabel", {}).get("value", "Unknown")
            count = item.get("symptomCount", {}).get("value", "0")
            print(f"  - {disease} (matches {count} symptoms)")
    else:
        print("❌ No symptom-to-disease data found")
    
    return len(bindings) if result and "results" in result else 0


def main():
    """Run all ontology tests."""
    print("\n" + "="*70)
    print("WIKIDATA ONTOLOGY VERIFICATION FOR v2.0 SIMILARITY SEARCH")
    print("="*70)
    print("Testing if Wikidata has sufficient data for ontology-based similarity...")
    
    results = {
        "Disease Hierarchy": test_disease_hierarchy(),
        "Disease-Symptom": test_disease_symptom_relationships(),
        "Drug-Disease": test_drug_disease_relationships(),
        "Drug Properties": test_drug_properties(),
        "Multi-hop Paths": test_multi_hop_paths(),
        "Symptom Search": test_symptom_to_disease_search()
    }
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    total_passed = sum(1 for count in results.values() if count > 0)
    total_tests = len(results)
    
    for test_name, count in results.items():
        status = "✅ PASS" if count > 0 else "❌ FAIL"
        print(f"{status} {test_name}: {count} results")
    
    print(f"\n📊 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed >= 4:
        print("\n✅ VERDICT: Wikidata has sufficient ontology data for v2.0!")
        print("   We can proceed with implementing the similarity-based search.")
    else:
        print("\n⚠️ VERDICT: Limited ontology data available.")
        print("   May need to supplement with additional data sources.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
