# 🏥 MedBot : Système d'Orientation Médicale Intelligent

**MedBot** est un chatbot expert conçu pour assister les patients dans leur pré-diagnostic et les orienter vers la spécialité médicale et le département hospitalier appropriés. Il combine la puissance du **Web Sémantique (Graphes de Connaissances)** et du **NLP (Traitement du Langage Naturel)**.

## 🎯 Objectif du Projet
L'objectif est de réduire l'engorgement des accueils hospitaliers en fournissant une orientation automatisée basée sur des données médicales structurées (Ontologies) et un raisonnement logique.

---

## 🏗️ Architecture du Système

Le projet est divisé en 3 couches principales :

1.  **Data Engineering Layer** : Nettoyage et consolidation de datasets hétérogènes (CSV) vers un format JSON normalisé.
2.  **Semantic Layer** : Création d'une ontologie médicale (T-Box) et d'un Graphe de Connaissances (A-Box) contenant plus de 2500 triplets RDF.
3.  **Application Layer** : Moteur NLP pour l'extraction de symptômes, interrogation du graphe via SPARQL et interface utilisateur.



---

## 🧩 Modules du Projet

* **`src/data_processing.py`** : Pipeline de nettoyage des données brutes et enrichissement métier (Urgences, Slots).
* **`src/build_graph.py`** : Générateur d'ontologie transformant les données en format Turtle (.ttl).
* **`notebooks/`** : Exploration des données et validation de la cohérence du graphe.
* **`data/ontology/`** : Stockage du graphe de connaissances et du schéma OWL.

---

## 🛠️ Technologies Utilisées

* **Langage** : Python 3.12
* **Web Sémantique** : RDFLib, Protégé (Modélisation OWL/Turtle)
* **NLP** : spaCy (Modèle `en_core_web_sm`)
* **Data** : Pandas, Matplotlib, Seaborn
* **LLM & RAG** : LangChain, Ollama (Mistral 7B)
* **Interface** : Streamlit (Chatbot UI)

---

## 🔄 Flux de Fonctionnement (Workflow)

```mermaid
graph TD
    A[Utilisateur : 'J'ai des éruptions cutanées'] --> B[NLP : Extraction du symptôme 'skin_rash']
    B --> C{Requête SPARQL}
    C --> D[Graphe RDF : Identification de la Maladie 'Acne']
    D --> E[Logique Métier : Récupération Spécialité + Département]
    E --> F[LLM : Formulation de la réponse humaine]
    F --> G[Bot : 'Je vous conseille de voir la Dermatologie au Bâtiment A']
