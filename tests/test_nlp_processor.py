"""
Unit Tests for MedBot NLP Processor
Tests symptom extraction, normalization, and language detection
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from nlp_processor import SymptomExtractor


@pytest.fixture
def extractor():
    """Create a symptom extractor instance"""
    data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'consolidated_medical_data.json'
    return SymptomExtractor(str(data_path))


class TestSymptomExtraction:
    """Test symptom extraction functionality"""
    
    def test_french_symptom_extraction(self, extractor):
        """Test extraction from French text"""
        # Use symptoms we know exist in dataset
        text = "J'ai une éruption cutanée et des démangeaisons"
        symptoms = extractor.extract_symptoms(text, language='fr')
        
        assert len(symptoms) > 0, f"Should extract at least one symptom, got: {symptoms}"
        symptom_names = [s['normalized'] for s in symptoms]
        assert 'skin_rash' in symptom_names or 'itching' in symptom_names
    
    def test_english_symptom_extraction(self, extractor):
        """Test extraction from English text"""
        text = "I have nausea and vomiting"
        symptoms = extractor.extract_symptoms(text, language='en')
        
        assert len(symptoms) > 0, "Should extract at least one symptom"
        symptom_names = [s['normalized'] for s in symptoms]
        assert 'nausea' in symptom_names or 'vomiting' in symptom_names
    
    def test_skin_symptoms(self, extractor):
        """Test dermatological symptoms"""
        text = "J'ai une éruption cutanée et des démangeaisons"
        symptoms = extractor.extract_symptoms(text, language='fr')
        
        assert len(symptoms) >= 2, "Should extract both skin symptoms"
        symptom_names = [s['normalized'] for s in symptoms]
        assert 'skin_rash' in symptom_names
        assert 'itching' in symptom_names
    
    def test_multi_symptom_extraction(self, extractor):
        """Test extraction of multiple symptoms"""
        text = "J'ai la diarrhée, des nausées et je me sens déshydraté"
        symptoms = extractor.extract_symptoms(text, language='fr')
        
        assert len(symptoms) >= 2, "Should extract multiple symptoms"
    
    def test_empty_input(self, extractor):
        """Test with empty input"""
        text = ""
        symptoms = extractor.extract_symptoms(text)
        
        assert symptoms == [], "Empty input should return empty list"
    
    def test_no_symptoms(self, extractor):
        """Test with text containing no medical symptoms"""
        text = "Je vais bien, merci"
        symptoms = extractor.extract_symptoms(text)
        
        # Should return empty or very few symptoms
        assert len(symptoms) == 0, "Non-medical text should not extract symptoms"


class TestSymptomNormalization:
    """Test symptom normalization"""
    
    def test_normalization(self, extractor):
        """Test symptom name normalization"""
        # Test that spaces are replaced with underscores
        normalized = extractor._normalize_symptom_name("skin rash")
        assert normalized == "skin_rash"
        
        normalized = extractor._normalize_symptom_name("chest pain")
        assert normalized == "chest_pain"
    
    def test_lowercase_conversion(self, extractor):
        """Test lowercase conversion"""
        normalized = extractor._normalize_symptom_name("FEVER")
        assert normalized == "fever"


class TestLanguageDetection:
    """Test language detection"""
    
    def test_french_detection(self, extractor):
        """Test French language detection"""
        text = "J'ai de la fièvre et des maux de tête"
        lang = extractor.detect_language(text)
        assert lang == "fr", "Should detect French"
    
    def test_english_detection(self, extractor):
        """Test English language detection"""
        text = "I have fever and headache"
        lang = extractor.detect_language(text)
        assert lang == "en", "Should detect English"


class TestConfidenceScoring:
    """Test confidence score assignment"""
    
    def test_confidence_range(self, extractor):
        """Test that confidence scores are in valid range"""
        text = "J'ai des nausées"  # Use symptom we know exists
        symptoms = extractor.extract_symptoms(text)
        
        if symptoms:  # Only test if symptoms were found
            for symptom in symptoms:
                assert 0.0 <= symptom['confidence'] <= 1.0, \
                    "Confidence should be between 0 and 1"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
