"""
LLM Engine with RAG for MedBot
Generates empathetic medical responses using Ollama and retrieved context
"""

from langchain_ollama import OllamaLLM
from typing import List, Dict, Optional
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedBotRAG:
    """RAG-based medical chatbot using Ollama LLM"""
    
    def __init__(
        self,
        ollama_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        language: str = "fr"
    ):
        """
        Initialize the MedBot RAG engine
        
        Args:
            ollama_base_url: Base URL for Ollama API
            model_name: Name of the model to use
            language: Default language ('fr' or 'en')
        """
        self.ollama_base_url = ollama_base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = model_name or os.getenv('MODEL_NAME', 'mistral')
        self.language = language
        
        # Initialize LLM
        self.llm = None
        self._initialize_llm()
        
        # Conversation history
        self.conversation_history = []
    
    def _initialize_llm(self):
        """Initialize connection to Ollama"""
        try:
            logger.info(f"Initializing Ollama LLM: {self.model_name} at {self.ollama_base_url}")
            
            self.llm = OllamaLLM(
                base_url=self.ollama_base_url,
                model=self.model_name,
                temperature=0.7  # Balance between creativity and consistency
            )
            
            # Test connection with a simple prompt
            logger.info(f"✓ Ollama LLM initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Ollama: {e}")
            logger.error("Make sure Ollama is running and the model is downloaded")
            logger.error(f"Run: ollama pull {self.model_name}")
            self.llm = None
    
    def _get_system_prompt(self, language: str = "fr") -> str:
        """Get the system prompt based on language"""
        if language == "fr":
            return """Tu es MedBot, un assistant médical intelligent et empathique basé sur une ontologie médicale.

Ton rôle:
- Analyser les symptômes du patient avec bienveillance
- Fournir des informations médicales préliminaires basées sur le graphe de connaissances
- Recommander la spécialité médicale appropriée
- Toujours encourager la consultation d'un professionnel de santé

IMPORTANT:
- Tu n'es PAS un médecin, tu es un assistant d'orientation
- Tes recommandations sont basées sur des données structurées, pas un diagnostic médical
- En cas d'urgence (douleur thoracique, difficulté respiratoire sévère), recommande une consultation immédiate

Structure ta réponse ainsi:
1. Reconnaissance empathique des symptômes
2. Analyse basée sur les données disponibles
3. Recommandation de spécialité et département
4. Niveau d'urgence
5. Précautions/conseils
6. Encouragement à consulter un professionnel"""
        else:
            return """You are MedBot, an intelligent and empathetic medical assistant based on a medical ontology.

Your role:
- Analyze patient symptoms with compassion
- Provide preliminary medical information based on the knowledge graph
- Recommend the appropriate medical specialty
- Always encourage consultation with a healthcare professional

IMPORTANT:
- You are NOT a doctor, you are a guidance assistant
- Your recommendations are based on structured data, not a medical diagnosis
- In case of emergency (chest pain, severe breathing difficulty), recommend immediate consultation

Structure your response:
1. Empathetic acknowledgment of symptoms
2. Analysis based on available data
3. Specialty and department recommendation
4. Urgency level
5. Precautions/advice
6. Encouragement to consult a professional"""
    
    def format_context(self, query_results: List[Dict]) -> str:
        """
        Format SPARQL query results into context for the LLM
        
        Args:
            query_results: List of disease dictionaries from query engine
            
        Returns:
            Formatted context string
        """
        if not query_results:
            return "Aucune maladie correspondante trouvée dans notre base de données."
        
        context_parts = []
        
        for i, disease in enumerate(query_results[:3], 1):  # Top 3 matches
            disease_info = f"""
Maladie #{i}: {disease['name']}
- Score de correspondance: {disease.get('match_percentage', 0):.1f}%
- Symptômes associés: {', '.join(disease.get('symptoms', [])[:5])}
- Symptômes concordants: {', '.join(disease.get('matched_symptoms', []))}
- Niveau d'urgence: {disease.get('urgency', 'moyen')}
"""
            
            # Add specialty info if available
            if 'specialty' in disease and disease['specialty']:
                spec = disease['specialty']
                if isinstance(spec, dict):
                    disease_info += f"- Spécialité recommandée: {spec.get('specialty', 'N/A')}\n"
                    disease_info += f"- Département: {spec.get('department', 'N/A')}\n"
                    disease_info += f"- Localisation: {spec.get('location', 'N/A')}\n"
            
            # Add precautions if available
            if 'precautions' in disease and disease['precautions']:
                precautions = disease['precautions'][:3]  # Top 3 precautions
                disease_info += f"- Précautions: {', '.join(precautions)}\n"
            
            context_parts.append(disease_info)
        
        return "\n".join(context_parts)
    
    def generate_response(
        self,
        user_input: str,
        query_results: List[Dict],
        language: Optional[str] = None
    ) -> str:
        """
        Generate a response using RAG
        
        Args:
            user_input: User's message
            query_results: Results from SPARQL query
            language: Response language
            
        Returns:
            Generated response
        """
        if self.llm is None:
            return self._fallback_response(query_results, language or self.language)
        
        lang = language or self.language
        
        # Format context from query results
        context = self.format_context(query_results)
        
        # Format conversation history
        history = "\n".join([
            f"{'Patient' if i % 2 == 0 else 'MedBot'}: {msg}"
            for i, msg in enumerate(self.conversation_history[-6:])  # Last 3 exchanges
        ])
        
        # Create the complete prompt
        system_prompt = self._get_system_prompt(lang)
        
        if lang == "fr":
            full_prompt = f"""{system_prompt}

Contexte du Graphe de Connaissances:
{context}

Historique de conversation:
{history}

Patient: {user_input}

Assistant MedBot:"""
        else:
            full_prompt = f"""{system_prompt}

Knowledge Graph Context:
{context}

Conversation History:
{history}

Patient: {user_input}

MedBot Assistant:"""
        
        try:
            # Generate response
            logger.info("Generating LLM response...")
            response = self.llm.invoke(full_prompt)
            
            # Add to conversation history
            self.conversation_history.append(user_input)
            self.conversation_history.append(response)
            
            logger.info("✓ Response generated")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(query_results, lang)
    
    def _fallback_response(self, query_results: List[Dict], language: str = "fr") -> str:
        """
        Generate a simple response without LLM (fallback)
        
        Args:
            query_results: Query results from knowledge graph
            language: Response language
        """
        if not query_results:
            if language == "fr":
                return """Je n'ai pas trouvé de correspondance exacte pour vos symptômes dans ma base de données.

Je vous recommande de consulter un médecin généraliste qui pourra vous examiner et établir un diagnostic approprié.

Si vos symptômes sont sévères ou s'aggravent, n'hésitez pas à vous rendre aux urgences."""
            else:
                return """I couldn't find an exact match for your symptoms in my database.

I recommend consulting a general practitioner who can examine you and make an appropriate diagnosis.

If your symptoms are severe or worsening, don't hesitate to go to the emergency room."""
        
        # Get the top match
        top_disease = query_results[0]
        
        if language == "fr":
            response = f"""Basé sur vos symptômes, voici mon analyse :

🔍 **Condition possible**: {top_disease['name']}
   - Correspondance: {top_disease.get('match_percentage', 0):.0f}%
   - Urgence: {top_disease.get('urgency', 'moyenne').upper()}

💊 **Recommandation**:
"""
            # Add specialty if available
            if 'specialty' in top_disease and top_disease['specialty']:
                spec = top_disease['specialty']
                if isinstance(spec, dict):
                    response += f"   - Spécialité: {spec.get('specialty', 'Médecine Générale')}\n"
                    response += f"   - Département: {spec.get('department', 'Consultations Externes')}\n"
            
            # Add precautions
            if 'precautions' in top_disease and top_disease['precautions']:
                response += f"\n⚠️ **Précautions**:\n"
                for precaution in top_disease['precautions'][:3]:
                    response += f"   - {precaution}\n"
            
            response += f"\n⚕️ **Important**: Cette analyse est indicative. Consultez un professionnel de santé pour un diagnostic précis."
            
        else:
            response = f"""Based on your symptoms, here's my analysis:

🔍 **Possible Condition**: {top_disease['name']}
   - Match: {top_disease.get('match_percentage', 0):.0f}%
   - Urgency: {top_disease.get('urgency', 'medium').upper()}

💊 **Recommendation**:
"""
            if 'specialty' in top_disease and top_disease['specialty']:
                spec = top_disease['specialty']
                if isinstance(spec, dict):
                    response += f"   - Specialty: {spec.get('specialty', 'General Medicine')}\n"
                    response += f"   - Department: {spec.get('department', 'Outpatient Clinic')}\n"
            
            if 'precautions' in top_disease and top_disease['precautions']:
                response += f"\n⚠️ **Precautions**:\n"
                for precaution in top_disease['precautions'][:3]:
                    response += f"   - {precaution}\n"
            
            response += f"\n⚕️ **Important**: This analysis is indicative. Consult a healthcare professional for an accurate diagnosis."
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")
    
    def get_conversation_history(self) -> List[str]:
        """Get the conversation history"""
        return self.conversation_history.copy()


# Test function
if __name__ == "__main__":
    # Test the RAG engine
    rag = MedBotRAG()
    
    print("\n" + "="*60)
    print("TESTING MEDBOT RAG ENGINE")
    print("="*60)
    
    # Mock query results
    mock_results = [
        {
            'name': 'Fungal infection',
            'match_percentage': 85.0,
            'urgency': 'low',
            'symptoms': ['skin_rash', 'itching', 'nodal_skin_eruptions'],
            'matched_symptoms': ['skin_rash', 'itching'],
            'specialty': {
                'specialty': 'Dermatology',
                'department': 'Skin Department',
                'location': 'Building A, 3rd Floor'
            },
            'precautions': [
                'bath twice',
                'use detol or neem in bathing water',
                'keep infected area dry'
            ]
        }
    ]
    
    print("\n1. Testing context formatting:")
    context = rag.format_context(mock_results)
    print(context)
    
    print("\n2. Testing response generation:")
    user_input = "J'ai une éruption cutanée et des démangeaisons"
    
    response = rag.generate_response(
        user_input=user_input,
        query_results=mock_results,
        language='fr'
    )
    
    print(f"\nUser: {user_input}")
    print(f"\nMedBot: {response}")