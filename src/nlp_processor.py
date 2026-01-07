"""
NLP Processor for MedBot
Extracts and normalizes medical symptoms from user input (French and English)
"""

import spacy
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SymptomExtractor:
    """Extract medical symptoms from natural language text"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the symptom extractor
        
        Args:
            data_path: Path to consolidated_medical_data.json
        """
        self.nlp_fr = None
        self.nlp_en = None
        self.symptoms_dict = {}
        self.symptom_synonyms = {}
        
        # Load data
        if data_path is None:
            data_path = os.getenv('DATA_PATH', 'data/processed/consolidated_medical_data.json')
        
        self._load_medical_data(data_path)
        self._load_nlp_models()
        self._build_symptom_dictionaries()
        
    def _load_nlp_models(self):
        """Load spaCy models for French and English"""
        try:
            logger.info("Loading spaCy French model...")
            self.nlp_fr = spacy.load("fr_core_news_sm")
            logger.info("✓ French model loaded")
        except OSError:
            logger.warning("French model not found. Download with: python -m spacy download fr_core_news_sm")
            self.nlp_fr = None
            
        try:
            logger.info("Loading spaCy English model...")
            self.nlp_en = spacy.load("en_core_web_sm")
            logger.info("✓ English model loaded")
        except OSError:
            logger.warning("English model not found. Download with: python -m spacy download en_core_web_sm")
            self.nlp_en = None
    
    def _load_medical_data(self, data_path: str):
        """Load medical data from consolidated JSON"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.medical_data = json.load(f)
            logger.info(f"✓ Loaded medical data from {data_path}")
        except FileNotFoundError:
            logger.error(f"Medical data file not found: {data_path}")
            self.medical_data = {"diseases": []}
    
    def _build_symptom_dictionaries(self):
        """Build symptom dictionary and synonyms from medical data"""
        # Extract all unique symptoms
        all_symptoms = set()
        
        for disease in self.medical_data.get("diseases", []):
            symptoms = disease.get("symptoms", [])
            # Symptoms are dictionaries with 'name' and 'severity'
            for symptom in symptoms:
                if isinstance(symptom, dict):
                    symptom_name = symptom.get('name', '')
                    if symptom_name:
                        all_symptoms.add(symptom_name)
                elif isinstance(symptom, str):
                    all_symptoms.add(symptom)
        
        # Create normalized symptom dictionary
        for symptom in all_symptoms:
            normalized = self._normalize_symptom_name(symptom)
            self.symptoms_dict[normalized] = symptom
            
        # Build synonym mappings (French <-> English)
        self._build_symptom_synonyms()
        
        logger.info(f"✓ Built dictionary with {len(self.symptoms_dict)} unique symptoms")
    
    def _build_symptom_synonyms(self):
        """Build French-English synonym mappings for common symptoms"""
        # Common medical translations
        self.symptom_synonyms = {
            # French -> English
            "fièvre": "fever",
            "toux": "cough",
            "mal de tête": "headache",
            "maux de tête": "headache",
            "céphalée": "headache",
            "douleur": "pain",
            "fatigue": "fatigue",
            "fatigué": "fatigue",
            "nausée": "nausea",
            "nausées": "nausea",
            "vomissement": "vomiting",
            "vomissements": "vomiting",
            "diarrhée": "diarrhea",
            "diarrhee": "diarrhea",  # without accent
            "déshydraté": "dehydration",
            "deshydrate": "dehydration",  # without accent
            "déshydratation": "dehydration",
            "constipation": "constipation",
            "éruption cutanée": "skin_rash",
            "eruption cutanee": "skin_rash",  # without accents
            "démangeaison": "itching",
            "demangeaison": "itching",  # without accent
            "démangeaisons": "itching",
            "essoufflement": "breathlessness",
            "difficulté à respirer": "breathlessness",
            "difficulte a respirer": "breathlessness",  # without accents
            "douleur thoracique": "chest_pain",
            "douleur abdominale": "stomach_pain",
            "mal de ventre": "stomach_pain",
            "mal au ventre": "stomach_pain",
            "vertige": "dizziness",
            "vertiges": "dizziness",
            "voyage": "travel",  # context word
            
            # English -> self (normalization)
            "headaches": "headache",
            "coughing": "cough",
            "painful": "pain",
            "stomach ache": "stomach_pain",
            "belly pain": "stomach_pain",
            "chest pain": "chest_pain",
            "skin rash": "skin_rash",
            "difficulty breathing": "breathlessness",
            "shortness of breath": "breathlessness",
            "dehydrated": "dehydration",
            "diarrhea": "diarrhoea",  # American vs British spelling
        }
    
    def _normalize_symptom_name(self, symptom: str) -> str:
        """Normalize symptom name (lowercase, replace spaces with underscores)"""
        return symptom.lower().strip().replace(' ', '_').replace('-', '_')
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words
        
        Args:
            text: Input text
            
        Returns:
            'fr' or 'en'
        """
        french_words = {'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 
                       'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une',
                       'ai', 'as', 'avons', 'suis', 'est', 'sont'}
        
        words = set(text.lower().split())
        french_count = len(words & french_words)
        
        return 'fr' if french_count >= 2 else 'en'
    
    def extract_symptoms(self, text: str, language: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Extract symptoms from user input text
        
        Args:
            text: User input text
            language: Language code ('fr' or 'en'), auto-detected if None
            
        Returns:
            List of dictionaries with 'symptom', 'normalized', 'confidence'
        """
        if language is None:
            language = self.detect_language(text)
        
        logger.info(f"Extracting symptoms from text (language: {language})")
        
        # Get appropriate NLP model
        nlp = self.nlp_fr if language == 'fr' else self.nlp_en
        
        if nlp is None:
            logger.warning(f"NLP model for {language} not available, using fallback")
            return self._fallback_extraction(text)
        
        # Process text with spaCy
        doc = nlp(text.lower())
        
        extracted_symptoms = []
        
        # Method 1: Look for known symptoms in text
        for symptom_key, symptom_value in self.symptoms_dict.items():
            if symptom_key in text.lower() or symptom_value.lower() in text.lower():
                extracted_symptoms.append({
                    'symptom': symptom_value,
                    'normalized': symptom_key,
                    'confidence': 0.9,
                    'method': 'exact_match'
                })
        
        # Method 2: Check synonyms
        for synonym, target in self.symptom_synonyms.items():
            if synonym in text.lower():
                normalized = self._normalize_symptom_name(target)
                if normalized in self.symptoms_dict:
                    extracted_symptoms.append({
                        'symptom': self.symptoms_dict[normalized],
                        'normalized': normalized,
                        'confidence': 0.85,
                        'method': 'synonym_match'
                    })
        
        # Method 3: Use noun chunks (potential symptoms)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            normalized = self._normalize_symptom_name(chunk_text)
            
            # Check if it's a known symptom
            if normalized in self.symptoms_dict:
                extracted_symptoms.append({
                    'symptom': self.symptoms_dict[normalized],
                    'normalized': normalized,
                    'confidence': 0.7,
                    'method': 'noun_chunk'
                })
        
        # Remove duplicates (keep highest confidence)
        unique_symptoms = {}
        for symptom in extracted_symptoms:
            key = symptom['normalized']
            if key not in unique_symptoms or symptom['confidence'] > unique_symptoms[key]['confidence']:
                unique_symptoms[key] = symptom
        
        result = list(unique_symptoms.values())
        
        # Sort by confidence
        result.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"✓ Extracted {len(result)} symptoms: {[s['symptom'] for s in result]}")
        
        return result
    
    def _fallback_extraction(self, text: str) -> List[Dict[str, any]]:
        """
        Fallback extraction when NLP models are not available
        Simple keyword matching
        """
        extracted_symptoms = []
        text_lower = text.lower()
        
        # Check all symptoms
        for symptom_key, symptom_value in self.symptoms_dict.items():
            if symptom_key in text_lower or symptom_value.lower() in text_lower:
                extracted_symptoms.append({
                    'symptom': symptom_value,
                    'normalized': symptom_key,
                    'confidence': 0.8,
                    'method': 'keyword_match'
                })
        
        # Check synonyms
        for synonym, target in self.symptom_synonyms.items():
            if synonym in text_lower:
                normalized = self._normalize_symptom_name(target)
                if normalized in self.symptoms_dict:
                    extracted_symptoms.append({
                        'symptom': self.symptoms_dict[normalized],
                        'normalized': normalized,
                        'confidence': 0.75,
                        'method': 'synonym_keyword'
                    })
        
        # Remove duplicates
        unique_symptoms = {}
        for symptom in extracted_symptoms:
            key = symptom['normalized']
            if key not in unique_symptoms:
                unique_symptoms[key] = symptom
        
        return list(unique_symptoms.values())
    
    def get_all_symptoms(self) -> List[str]:
        """Get list of all known symptoms"""
        return list(self.symptoms_dict.values())


# Test function
if __name__ == "__main__":
    # Test the extractor
    extractor = SymptomExtractor()
    
    # Test cases
    test_inputs = [
        "J'ai de la fièvre et je tousse beaucoup",
        "I have a headache and feel dizzy",
        "Je ressens une douleur abdominale",
        "I have skin rash and itching"
    ]
    
    print("\n" + "="*60)
    print("TESTING SYMPTOM EXTRACTOR")
    print("="*60)
    
    for text in test_inputs:
        print(f"\nInput: {text}")
        symptoms = extractor.extract_symptoms(text)
        print(f"Extracted symptoms:")
        for symptom in symptoms:
            print(f"  - {symptom['symptom']} (confidence: {symptom['confidence']:.2f})")
