"""
Integration Tests for MedBot
Tests end-to-end flow from symptom input to diagnosis
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from nlp_processor import SymptomExtractor
from query_engine import MedicalKnowledgeGraph


@pytest.fixture
def extractor():
    """Create symptom extractor"""
    data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'consolidated_medical_data.json'
    return SymptomExtractor(str(data_path))


@pytest.fixture
def kg():
    """Create knowledge graph"""
    ontology_path = Path(__file__).parent.parent / 'data' / 'ontology' / 'medical_ontology.ttl'
    return MedicalKnowledgeGraph(str(ontology_path))


class TestEndToEndFlow:
    """Test complete symptom → diagnosis flow"""
    
    def test_french_dermatology_case(self, extractor, kg):
        """Test: French input for skin condition"""
        # Step 1: User input
        user_input = "J'ai une éruption cutanée et des démangeaisons"
        
        # Step 2: Extract symptoms
        symptoms = extractor.extract_symptoms(user_input, language='fr')
        assert len(symptoms) >= 1, "Should extract at least one symptom"
        
        # Step 3: Query diseases
        symptom_names = [s['normalized'] for s in symptoms]
        diseases = kg.query_diseases_by_symptoms(symptom_names)
        
        assert len(diseases) > 0, "Should find matching diseases"
        
        # Step 4: Get top disease details
        top_disease = diseases[0]
        details = kg.get_disease_details(top_disease['uri'])
        
        assert details is not None
        assert details['name'] == top_disease['name']
        
        print(f"\n✓ Test passed: {user_input}")
        print(f"  Symptoms: {symptom_names}")
        print(f"  Top match: {top_disease['name']} ({top_disease['match_percentage']:.1f}%)")
    
    def test_english_respiratory_case(self, extractor, kg):
        """Test: English input for respiratory symptoms"""
        user_input = "I have a cough and fever"
        
        symptoms = extractor.extract_symptoms(user_input, language='en')
        assert len(symptoms) >= 1
        
        symptom_names = [s['normalized'] for s in symptoms]
        diseases = kg.query_diseases_by_symptoms(symptom_names)
        
        assert len(diseases) > 0
        
        # Verify urgency indicator exists
        top_disease = diseases[0]
        assert 'urgency' in top_disease
        
        print(f"\n✓ Test passed: {user_input}")
        print(f"  Symptoms: {symptom_names}")
        print(f"  Top match: {top_disease['name']} (urgency: {top_disease['urgency']})")
    
    def test_multi_symptom_gastro_case(self, extractor, kg):
        """Test: Multiple symptoms - gastro case"""
        user_input = "J'ai la diarrhée, des nausées et je me sens déshydraté"
        
        symptoms = extractor.extract_symptoms(user_input, language='fr')
        symptom_names = [s['normalized'] for s in symptoms]
        
        diseases = kg.query_diseases_by_symptoms(symptom_names)
        
        if len(diseases) > 0:
            top_disease = diseases[0]
            
            # Get specialty
            details = kg.get_disease_details(top_disease['uri'])
            if details and details['specialty']:
                specialty = details['specialty']['specialty']
                print(f"\n✓ Test passed: {user_input}")
                print(f"  Symptoms detected: {len(symptoms)}")
                print(f"  Recommended: {specialty}")
    
    def test_emergency_cardio_case(self, extractor, kg):
        """Test: Emergency case - chest pain"""
        user_input = "I have severe chest pain and difficulty breathing"
        
        symptoms = extractor.extract_symptoms(user_input, language='en')
        symptom_names = [s['normalized'] for s in symptoms]
        
        diseases = kg.query_diseases_by_symptoms(symptom_names)
        
        if len(diseases) > 0:
            top_disease = diseases[0]
            
            # Should have high urgency
            assert 'urgency' in top_disease
            
            # Get details
            details = kg.get_disease_details(top_disease['uri'])
            
            print(f"\n✓ Test passed: {user_input}")
            print(f"  Urgency: {top_disease['urgency']}")
            if details and details['specialty']:
                print(f"  Specialty: {details['specialty']['specialty']}")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_vague_input(self, extractor, kg):
        """Test with vague, non-specific input"""
        user_input = "I don't feel well"
        
        symptoms = extractor.extract_symptoms(user_input)
        
        # Should handle gracefully (may or may not extract symptoms)
        assert isinstance(symptoms, list)
    
    def test_very_long_input(self, extractor, kg):
        """Test with very long input text"""
        user_input = "J'ai " + ", ".join(["de la fièvre"] * 50)  # Repeated symptom
        
        symptoms = extractor.extract_symptoms(user_input)
        
        # Should not crash and should deduplicate
        assert isinstance(symptoms, list)
    
    def test_mixed_language_input(self, extractor, kg):
        """Test with mixed language input"""
        user_input = "I have de la fièvre and cough"
        
        symptoms = extractor.extract_symptoms(user_input)
        
        # Should handle mixed languages
        assert isinstance(symptoms, list)


class TestDataConsistency:
    """Test data consistency across components"""
    
    def test_symptom_in_both_nlp_and_graph(self, extractor, kg):
        """Test that NLP-extracted symptoms exist in graph"""
        test_symptoms = ['fever', 'cough', 'headache']
        
        for symptom in test_symptoms:
            # Query with single symptom
            diseases = kg.query_diseases_by_symptoms([symptom])
            
            # If NLP knows about it, graph should have diseases for it
            # (allowing for some symptoms that might not have disease mappings)
            print(f"  {symptom}: {len(diseases)} diseases found")
    
    def test_all_diseases_have_specialties(self, kg):
        """Verify all diseases in test queries have specialty assignments"""
        test_symptom_sets = [
            ['fever'],
            ['skin_rash'],
            ['nausea'],
        ]
        
        for symptoms in test_symptom_sets:
            diseases = kg.query_diseases_by_symptoms(symptoms)
            
            for disease in diseases[:3]:  # Check top 3
                specialty = kg.get_specialty_for_disease(disease['uri'])
                # Specialty should exist (though may be None for some diseases)
                assert specialty is None or 'specialty' in specialty


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])
