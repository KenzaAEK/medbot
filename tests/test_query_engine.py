"""
Unit Tests for MedBot Query Engine
Tests SPARQL queries, disease matching, and ranking
"""

import pytest
import sys
from pathlib import Path

# Add src to path  
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from query_engine import MedicalKnowledgeGraph


@pytest.fixture
def kg():
    """Create a knowledge graph instance"""
    ontology_path = Path(__file__).parent.parent / 'data' / 'ontology' / 'medical_ontology.ttl'
    return MedicalKnowledgeGraph(str(ontology_path))


class TestGraphLoading:
    """Test knowledge graph loading"""
    
    def test_graph_loaded(self, kg):
        """Test that graph loads successfully"""
        assert len(kg.graph) > 0, "Graph should contain triples"
        assert len(kg.graph) >= 1000, "Graph should have at least 1000 triples"
    
    def test_graph_statistics(self, kg):
        """Test graph statistics retrieval"""
        stats = kg.get_graph_statistics()
        
        assert stats['total_triples'] > 0
        assert stats['diseases'] > 0
        assert stats['symptoms'] > 0
        assert stats['departments'] > 0


class TestDiseaseQuerying:
    """Test disease querying functionality"""
    
    def test_query_by_single_symptom(self, kg):
        """Test querying with a single symptom"""
        symptoms = ['nausea']  # Use symptom that exists
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        assert len(diseases) > 0, "Should find diseases with nausea"
        assert all('name' in d for d in diseases), "All results should have name"
        assert all('match_score' in d for d in diseases), "All results should have match_score"
    
    def test_query_by_multiple_symptoms(self, kg):
        """Test querying with multiple symptoms"""
        symptoms = ['skin_rash', 'itching']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        assert len(diseases) > 0, "Should find diseases matching skin symptoms"
        
        # Check that matched_symptoms are populated
        for disease in diseases:
            assert 'matched_symptoms' in disease
            assert len(disease['matched_symptoms']) > 0
    
    def test_query_with_nonexistent_symptom(self, kg):
        """Test querying with symptom that doesn't exist"""
        symptoms = ['nonexistent_symptom_xyz']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        # Should return empty list or no matches
        assert len(diseases) == 0, "Should not find matches for nonexistent symptom"
    
    def test_empty_symptom_list(self, kg):
        """Test querying with empty symptom list"""
        symptoms = []
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        assert diseases == [], "Empty symptom list should return empty results"


class TestDiseaseRanking:
    """Test disease ranking algorithm"""
    
    def test_ranking_order(self, kg):
        """Test that results are ranked by relevance"""
        symptoms = ['nausea', 'vomiting']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        if len(diseases) > 1:
            # First disease should have highest or equal match score
            for i in range(len(diseases) - 1):
                assert diseases[i]['match_score'] >= diseases[i+1]['match_score'], \
                    "Diseases should be sorted by match score (descending)"
    
    def test_match_score_range(self, kg):
        """Test that match scores are in valid range"""
        symptoms = ['fever', 'cough']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        for disease in diseases:
            # Score should be between 0 and 10
            assert 0 <= disease['match_score'] <= 10, \
                f"Match score {disease['match_score']} out of range for {disease['name']}"
    
    def test_match_percentage(self, kg):
        """Test match percentage calculation"""
        symptoms = ['itching']  # Use valid symptom
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        for disease in diseases:
            # Percentage should be between 0 and 100
            assert 0 <= disease['match_percentage'] <= 100, \
                f"Match percentage {disease['match_percentage']} out of range"


class TestDiseaseDetails:
    """Test disease detail retrieval"""
    
    def test_get_disease_details(self, kg):
        """Test retrieving disease details"""
        symptoms = ['fever']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        if diseases:
            disease_uri = diseases[0]['uri']
            details = kg.get_disease_details(disease_uri)
            
            assert details is not None
            assert 'name' in details
            assert 'urgency' in details
            assert 'symptoms' in details
    
    def test_specialty_retrieval(self, kg):
        """Test specialty information retrieval"""
        symptoms = ['skin_rash']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        if diseases:
            disease_uri = diseases[0]['uri']
            specialty = kg.get_specialty_for_disease(disease_uri)
            
            # Specialty may or may not exist for all diseases
            if specialty:
                assert 'specialty' in specialty
                assert 'department' in specialty
    
    def test_precautions_retrieval(self, kg):
        """Test precautions retrieval"""
        symptoms = ['fever']
        diseases = kg.query_diseases_by_symptoms(symptoms)
        
        if diseases:
            disease_uri = diseases[0]['uri']
            precautions = kg.get_precautions_for_disease(disease_uri)
            
            # Precautions may or may not exist
            assert isinstance(precautions, list)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_all_specialties(self, kg):
        """Test listing all specialties"""
        specialties = kg.get_all_specialties()
        
        assert isinstance(specialties, list)
        assert len(specialties) > 0, "Should have at least one specialty"
    
    def test_get_all_departments(self, kg):
        """Test listing all departments"""
        departments = kg.get_all_departments()
        
        assert isinstance(departments, list)
        assert len(departments) > 0, "Should have at least one department"
        
        # Check structure
        if departments:
            assert 'name' in departments[0]
            assert 'location' in departments[0]
    
    def test_search_by_disease_name(self, kg):
        """Test disease name search"""
        results = kg.search_by_disease_name("diabetes")
        
        # Should find diabetes-related diseases
        assert isinstance(results, list)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
