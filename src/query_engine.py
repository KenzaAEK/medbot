"""
SPARQL Query Engine for MedBot
Queries the medical knowledge graph to find diseases, specialties, and recommendations
"""

from rdflib import Graph, Namespace, RDF, RDFS, Literal
from typing import List, Dict, Optional, Tuple
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define namespaces
MED = Namespace("http://medbot.org/ontology#")


class MedicalKnowledgeGraph:
    """Query the medical knowledge graph using SPARQL"""
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize the knowledge graph
        
        Args:
            ontology_path: Path to medical_ontology.ttl file
        """
        self.graph = Graph()
        
        if ontology_path is None:
            ontology_path = os.getenv('ONTOLOGY_PATH', 'data/ontology/medical_ontology.ttl')
        
        self.ontology_path = ontology_path
        self._load_graph()
        
        # Bind namespaces
        self.graph.bind("med", MED)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
    
    def _load_graph(self):
        """Load the RDF graph from Turtle file"""
        try:
            logger.info(f"Loading medical ontology from {self.ontology_path}")
            self.graph.parse(self.ontology_path, format='turtle')
            logger.info(f"✓ Loaded graph with {len(self.graph)} triples")
        except FileNotFoundError:
            logger.error(f"Ontology file not found: {self.ontology_path}")
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
    
    def get_graph_statistics(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph"""
        stats = {
            'total_triples': len(self.graph),
            'diseases': 0,
            'symptoms': 0,
            'specialties': 0,
            'departments': 0
        }
        
        # Count diseases
        query = """
        SELECT (COUNT(DISTINCT ?disease) as ?count)
        WHERE {
            ?disease rdf:type med:Disease .
        }
        """
        result = list(self.graph.query(query, initNs={'med': MED, 'rdf': RDF}))
        if result:
            stats['diseases'] = int(result[0][0])
        
        # Count symptoms
        query = """
        SELECT (COUNT(DISTINCT ?symptom) as ?count)
        WHERE {
            ?symptom rdf:type med:Symptom .
        }
        """
        result = list(self.graph.query(query, initNs={'med': MED, 'rdf': RDF}))
        if result:
            stats['symptoms'] = int(result[0][0])
        
        # Count specialties
        query = """
        SELECT (COUNT(DISTINCT ?specialty) as ?count)
        WHERE {
            ?specialty rdf:type med:MedicalSpecialty .
        }
        """
        result = list(self.graph.query(query, initNs={'med': MED, 'rdf': RDF}))
        if result:
            stats['specialties'] = int(result[0][0])
        
        # Count departments
        query = """
        SELECT (COUNT(DISTINCT ?dept) as ?count)
        WHERE {
            ?dept rdf:type med:Department .
        }
        """
        result = list(self.graph.query(query, initNs={'med': MED, 'rdf': RDF}))
        if result:
            stats['departments'] = int(result[0][0])
        
        return stats
    
    def query_diseases_by_symptoms(self, symptom_names: List[str]) -> List[Dict]:
        """
        Find diseases that match the given symptoms
        
        Args:
            symptom_names: List of symptom names (normalized)
            
        Returns:
            List of disease information dictionaries
        """
        if not symptom_names:
            logger.warning("No symptoms provided for query")
            return []
        
        logger.info(f"Querying diseases for symptoms: {symptom_names}")
        
        # Build SPARQL query
        # We'll find all diseases that have at least one of the symptoms
        symptom_filter = ", ".join([f'"{s}"' for s in symptom_names])
        
        query = f"""
        SELECT DISTINCT ?disease ?diseaseName ?description ?urgency
        WHERE {{
            ?disease rdf:type med:Disease .
            ?disease med:diseaseName ?diseaseName .
            ?disease med:hasSymptom ?symptom .
            ?symptom med:symptomName ?symptomName .
            FILTER(?symptomName IN ({symptom_filter}))
            OPTIONAL {{ ?disease med:description ?description }}
            OPTIONAL {{ ?disease med:urgencyLevel ?urgency }}
        }}
        """
        
        results = []
        try:
            qres = self.graph.query(query, initNs={'med': MED, 'rdf': RDF})
            
            for row in qres:
                disease_uri = str(row.disease)
                disease_name = str(row.diseaseName) if row.diseaseName else "Unknown"
                description = str(row.description) if row.description else ""
                urgency = str(row.urgency) if row.urgency else "medium"
                
                # Get all symptoms for this disease
                disease_symptoms = self._get_disease_symptoms(disease_uri)
                
                # Calculate match score
                match_score = self._calculate_match_score(symptom_names, disease_symptoms)
                
                results.append({
                    'uri': disease_uri,
                    'name': disease_name,
                    'description': description,
                    'urgency': urgency,
                    'symptoms': disease_symptoms,
                    'matched_symptoms': [s for s in symptom_names if s in disease_symptoms],
                    'match_score': match_score,
                    'match_percentage': match_score * 10  # Score is 0-10, percentage is 0-100
                })
            
            # Rank by match score
            results = self.rank_diseases(results, symptom_names)
            
            logger.info(f"✓ Found {len(results)} matching diseases")
            
        except Exception as e:
            logger.error(f"Error executing SPARQL query: {e}")
        
        return results
    
    def _get_disease_symptoms(self, disease_uri: str) -> List[str]:
        """Get all symptoms for a specific disease"""
        query = f"""
        SELECT ?symptomName
        WHERE {{
            <{disease_uri}> med:hasSymptom ?symptom .
            ?symptom med:symptomName ?symptomName .
        }}
        """
        
        symptoms = []
        try:
            qres = self.graph.query(query, initNs={'med': MED})
            symptoms = [str(row.symptomName) for row in qres]
        except Exception as e:
            logger.error(f"Error getting symptoms for disease: {e}")
        
        return symptoms
    
    def _calculate_match_score(self, user_symptoms: List[str], disease_symptoms: List[str]) -> float:
        """
        Calculate a match score between user symptoms and disease symptoms
        
        Returns a score from 0-10 where:
        - Perfect match (all user symptoms found) = 10
        - Partial matches get proportional scores
        """
        if not user_symptoms or not disease_symptoms:
            return 0.0
        
        matched = set(user_symptoms) & set(disease_symptoms)
        
        # Calculate percentage of user symptoms that matched
        match_ratio = len(matched) / len(user_symptoms)
        
        # Score out of 10
        score = match_ratio * 10
        
        return min(score, 10.0)  # Cap at 10
    
    def rank_diseases(self, diseases: List[Dict], user_symptoms: List[str]) -> List[Dict]:
        """
        Rank diseases by match score and urgency
        
        Args:
            diseases: List of disease dictionaries
            user_symptoms: User's symptoms
            
        Returns:
            Sorted list of diseases (best match first)
        """
        # Sort by match_score (descending) and urgency (high first)
        urgency_priority = {'high': 3, 'medium': 2, 'low': 1}
        
        def sort_key(disease):
            urgency_score = urgency_priority.get(disease.get('urgency', 'medium').lower(), 2)
            match_score = disease.get('match_score', 0)
            return (match_score, urgency_score)
        
        diseases.sort(key=sort_key, reverse=True)
        
        return diseases
    
    def get_disease_details(self, disease_uri: str) -> Optional[Dict]:
        """
        Get complete information about a disease
        
        Args:
            disease_uri: URI of the disease
            
        Returns:
            Dictionary with disease details
        """
        query = f"""
        SELECT ?diseaseName ?description ?urgency
        WHERE {{
            <{disease_uri}> rdf:type med:Disease .
            <{disease_uri}> med:diseaseName ?diseaseName .
            OPTIONAL {{ <{disease_uri}> med:description ?description }}
            OPTIONAL {{ <{disease_uri}> med:urgencyLevel ?urgency }}
        }}
        """
        
        try:
            qres = list(self.graph.query(query, initNs={'med': MED, 'rdf': RDF}))
            
            if qres:
                row = qres[0]
                return {
                    'uri': disease_uri,
                    'name': str(row.diseaseName),
                    'description': str(row.description) if row.description else "",
                    'urgency': str(row.urgency) if row.urgency else "medium",
                    'symptoms': self._get_disease_symptoms(disease_uri),
                    'specialty': self.get_specialty_for_disease(disease_uri),
                    'precautions': self.get_precautions_for_disease(disease_uri)
                }
        except Exception as e:
            logger.error(f"Error getting disease details: {e}")
        
        return None
    
    def get_specialty_for_disease(self, disease_uri: str) -> Optional[Dict]:
        """Get the medical specialty that treats this disease"""
        query = f"""
        SELECT ?specialtyName ?department ?location
        WHERE {{
            <{disease_uri}> med:treatedBy ?specialty .
            ?specialty med:specialtyName ?specialtyName .
            OPTIONAL {{
                ?specialty med:belongsToDepartment ?dept .
                ?dept med:departmentName ?department .
                OPTIONAL {{ ?dept med:location ?location }}
            }}
        }}
        """
        
        try:
            qres = list(self.graph.query(query, initNs={'med': MED}))
            
            if qres:
                row = qres[0]
                return {
                    'specialty': str(row.specialtyName),
                    'department': str(row.department) if row.department else "General",
                    'location': str(row.location) if row.location else "Main Building"
                }
        except Exception as e:
            logger.error(f"Error getting specialty: {e}")
        
        return None
    
    def get_precautions_for_disease(self, disease_uri: str) -> List[str]:
        """Get precautions/recommendations for a disease"""
        query = f"""
        SELECT ?precaution
        WHERE {{
            <{disease_uri}> med:hasPrecaution ?precaution .
        }}
        """
        
        precautions = []
        try:
            qres = self.graph.query(query, initNs={'med': MED})
            precautions = [str(row.precaution) for row in qres]
        except Exception as e:
            logger.error(f"Error getting precautions: {e}")
        
        return precautions
    
    def search_by_disease_name(self, disease_name: str) -> List[Dict]:
        """Search diseases by name (partial match)"""
        query = f"""
        SELECT ?disease ?diseaseName ?description
        WHERE {{
            ?disease rdf:type med:Disease .
            ?disease med:diseaseName ?diseaseName .
            FILTER(CONTAINS(LCASE(?diseaseName), LCASE("{disease_name}")))
            OPTIONAL {{ ?disease med:description ?description }}
        }}
        LIMIT 10
        """
        
        results = []
        try:
            qres = self.graph.query(query, initNs={'med': MED, 'rdf': RDF})
            
            for row in qres:
                results.append({
                    'uri': str(row.disease),
                    'name': str(row.diseaseName),
                    'description': str(row.description) if row.description else ""
                })
        except Exception as e:
            logger.error(f"Error searching diseases: {e}")
        
        return results
    
    def get_all_specialties(self) -> List[str]:
        """Get list of all medical specialties"""
        query = """
        SELECT DISTINCT ?specialtyName
        WHERE {
            ?specialty rdf:type med:Specialty .
            ?specialty med:specialtyName ?specialtyName .
        }
        ORDER BY ?specialtyName
        """
        
        specialties = []
        try:
            qres = self.graph.query(query, initNs={'med': MED, 'rdf': RDF})
            specialties = [str(row.specialtyName) for row in qres]
        except Exception as e:
            logger.error(f"Error getting specialties: {e}")
        
        return specialties
    
    def get_all_departments(self) -> List[Dict]:
        """Get list of all departments"""
        query = """
        SELECT ?deptName ?location
        WHERE {
            ?dept rdf:type med:Department .
            ?dept med:departmentName ?deptName .
            OPTIONAL { ?dept med:location ?location }
        }
        ORDER BY ?deptName
        """
        
        departments = []
        try:
            qres = self.graph.query(query, initNs={'med': MED, 'rdf': RDF})
            
            for row in qres:
                departments.append({
                    'name': str(row.deptName),
                    'location': str(row.location) if row.location else "Unknown"
                })
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
        
        return departments


# Test function
if __name__ == "__main__":
    # Test the query engine
    kg = MedicalKnowledgeGraph()
    
    print("\n" + "="*60)
    print("TESTING MEDICAL KNOWLEDGE GRAPH")
    print("="*60)
    
    # Test 1: Graph statistics
    print("\n1. Graph Statistics:")
    stats = kg.get_graph_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 2: Query by symptoms
    print("\n2. Query by symptoms:")
    test_symptoms = ['skin_rash', 'itching']
    diseases = kg.query_diseases_by_symptoms(test_symptoms)
    
    print(f"   Symptoms: {test_symptoms}")
    print(f"   Found {len(diseases)} diseases:")
    
    for disease in diseases[:3]:  # Show top 3
        print(f"\n   - {disease['name']}")
        print(f"     Match score: {disease['match_score']:.2f} ({disease['match_percentage']:.1f}%)")
        print(f"     Matched symptoms: {disease['matched_symptoms']}")
        print(f"     Urgency: {disease['urgency']}")
    
    # Test 3: Get disease details
    if diseases:
        print("\n3. Disease Details:")
        details = kg.get_disease_details(diseases[0]['uri'])
        if details:
            print(f"   Disease: {details['name']}")
            print(f"   Specialty: {details['specialty']}")
            print(f"   Precautions: {details['precautions'][:2] if details['precautions'] else 'None'}")
    
    # Test 4: List specialties
    print("\n4. Available Specialties:")
    specialties = kg.get_all_specialties()
    print(f"   Total: {len(specialties)}")
    print(f"   Sample: {specialties[:5]}")