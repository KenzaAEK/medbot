"""
MedBot - Medical Chatbot Interface
Streamlit application for symptom-based medical guidance
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from nlp_processor import SymptomExtractor
from query_engine import MedicalKnowledgeGraph
from llm_engine import MedBotRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MedBot - Assistant Médical",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .urgency-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        border-radius: 5px;
    }
    
    .urgency-medium {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
        border-radius: 5px;
    }
    
    .urgency-low {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 10px;
        border-radius: 5px;
    }
    
    .disease-card {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def load_components():
    """Load and cache the MedBot components"""
    try:
        logger.info("Loading MedBot components...")
        
        # Initialize components
        symptom_extractor = SymptomExtractor()
        knowledge_graph = MedicalKnowledgeGraph()
        rag_engine = MedBotRAG()
        
        logger.info("✓ All components loaded successfully")
        
        return symptom_extractor, knowledge_graph, rag_engine
    
    except Exception as e:
        logger.error(f"Error loading components: {e}")
        st.error(f"Erreur lors du chargement des composants: {e}")
        return None, None, None


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'language' not in st.session_state:
        st.session_state.language = 'fr'
    
    if 'conversation_count' not in st.session_state:
        st.session_state.conversation_count = 0
    
    # Cache components in session state to avoid reloading
    if 'components_loaded' not in st.session_state:
        st.session_state.components_loaded = False


def display_disease_card(disease: dict, rank: int):
    """Display a disease information card"""
    urgency = disease.get('urgency', 'medium').lower()
    urgency_class = f"urgency-{urgency}"
    
    st.markdown(f"""
    <div class="disease-card">
        <h4>#{rank} - {disease['name']}</h4>
        <p><strong>Correspondance:</strong> {disease.get('match_percentage', 0):.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Urgency indicator
    urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    urgency_text = {"high": "HAUTE", "medium": "MOYENNE", "low": "BASSE"}
    
    st.markdown(f"""
    <div class="{urgency_class}">
        {urgency_emoji.get(urgency, '🟡')} <strong>Urgence:</strong> {urgency_text.get(urgency, 'MOYENNE')}
    </div>
    """, unsafe_allow_html=True)
    
    # Matched symptoms
    if disease.get('matched_symptoms'):
        st.write("**Symptômes concordants:**")
        st.write(", ".join(disease['matched_symptoms']))
    
    # Specialty info
    if 'specialty' in disease and disease['specialty']:
        spec = disease['specialty']
        if isinstance(spec, dict):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Spécialité:** {spec.get('specialty', 'N/A')}")
            with col2:
                st.write(f"**Département:** {spec.get('department', 'N/A')}")
            
            if spec.get('location'):
                st.write(f"**Localisation:** {spec['location']}")
    
    # Precautions
    if disease.get('precautions'):
        with st.expander("📋 Précautions recommandées"):
            for i, precaution in enumerate(disease['precautions'][:5], 1):
                st.write(f"{i}. {precaution}")


def main():
    """Main application"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        🏥 MedBot - Assistant Médical Intelligent
    </div>
    """, unsafe_allow_html=True)
    
    # Load components (only once per session)
    if not st.session_state.components_loaded:
        with st.spinner("Chargement des composants médicaux..."):
            symptom_extractor, knowledge_graph, rag_engine = load_components()
            
            if all([symptom_extractor, knowledge_graph, rag_engine]):
                st.session_state.symptom_extractor = symptom_extractor
                st.session_state.knowledge_graph = knowledge_graph
                st.session_state.rag_engine = rag_engine
                st.session_state.components_loaded = True
            else:
                st.error("❌ Erreur: Impossible de charger les composants nécessaires")
                st.stop()
    
    # Get components from session state
    symptom_extractor = st.session_state.symptom_extractor
    knowledge_graph = st.session_state.knowledge_graph
    rag_engine = st.session_state.rag_engine
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Language selector
        language = st.selectbox(
            "Langue / Language",
            options=['fr', 'en'],
            format_func=lambda x: "🇫🇷 Français" if x == 'fr' else "🇬🇧 English",
            key='language_selector'
        )
        st.session_state.language = language
        
        st.divider()
        
        # System statistics
        st.header("📊 Statistiques du Système")
        
        try:
            stats = knowledge_graph.get_graph_statistics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Maladies", stats.get('diseases', 0))
                st.metric("Symptômes", stats.get('symptoms', 0))
            with col2:
                st.metric("Spécialités", stats.get('specialties', 0))
                st.metric("Départements", stats.get('departments', 0))
            
            st.metric("Triplets RDF", stats.get('total_triples', 0))
        
        except Exception as e:
            st.error(f"Erreur stats: {e}")
        
        st.divider()
        
        # About
        st.header("ℹ️ À propos")
        st.write("""
        MedBot est un assistant médical basé sur:
        - 🧠 Ontologie médicale (RDF/OWL)
        - 🔍 Extraction NLP des symptômes
        - 🤖 LLM (Mistral via Ollama)
        - 📊 Requêtes SPARQL
        """)
        
        st.divider()
        
        # Reset conversation
        if st.button("🔄 Nouvelle Conversation", use_container_width=True):
            st.session_state.messages = []
            rag_engine.reset_conversation()
            st.session_state.conversation_count += 1
            st.rerun()
        
        # Disclaimer
        st.warning("""
        ⚠️ **Avertissement**
        
        MedBot est un outil d'orientation, PAS un diagnostic médical. 
        
        Consultez toujours un professionnel de santé.
        """)
    
    # Main chat interface
    st.header("💬 Conversation")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display disease cards if available
            if message["role"] == "assistant" and "diseases" in message:
                st.subheader("🔍 Analyses détaillées")
                for i, disease in enumerate(message["diseases"][:3], 1):
                    with st.expander(f"Voir détails - {disease['name']}"):
                        display_disease_card(disease, i)
    
    # Chat input
    if prompt := st.chat_input("Décrivez vos symptômes..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process the message
        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                try:
                    # Step 1: Extract symptoms
                    symptoms = symptom_extractor.extract_symptoms(
                        prompt,
                        language=st.session_state.language
                    )
                    
                    if not symptoms:
                        response = "Je n'ai pas pu identifier de symptômes spécifiques. Pouvez-vous décrire vos symptômes plus précisément ?" if st.session_state.language == 'fr' else "I couldn't identify specific symptoms. Can you describe your symptoms more precisely?"
                        st.markdown(response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response
                        })
                    else:
                        # Show extracted symptoms
                        st.info(f"**Symptômes détectés:** {', '.join([s['symptom'] for s in symptoms])}")
                        
                        # Step 2: Query knowledge graph
                        symptom_names = [s['normalized'] for s in symptoms]
                        diseases = knowledge_graph.query_diseases_by_symptoms(symptom_names)
                        
                        # Enrich disease data with full details
                        for disease in diseases[:3]:  # Top 3
                            details = knowledge_graph.get_disease_details(disease['uri'])
                            if details:
                                disease['specialty'] = details.get('specialty')
                                disease['precautions'] = details.get('precautions', [])
                        
                        # Step 3: Generate LLM response
                        response = rag_engine.generate_response(
                            user_input=prompt,
                            query_results=diseases,
                            language=st.session_state.language
                        )
                        
                        st.markdown(response)
                        
                        # Store message with disease data
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "diseases": diseases[:3]
                        })
                        
                        # Display disease cards
                        if diseases:
                            st.subheader("🔍 Analyses détaillées")
                            for i, disease in enumerate(diseases[:3], 1):
                                with st.expander(f"Voir détails - {disease['name']}", expanded=(i==1)):
                                    display_disease_card(disease, i)
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    error_msg = f"Erreur lors du traitement: {e}" if st.session_state.language == 'fr' else f"Error processing: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Footer
    st.markdown("""
    <div class="footer">
        Made with ❤️ using Streamlit, spaCy, RDFLib, and Ollama<br>
        MedBot © 2026 - Knowledge Graph Medical Assistant
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
