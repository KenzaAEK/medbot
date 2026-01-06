from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import json
import os

# --- 1. DÉFINITION DES NAMESPACES (Le "Vocabulaire") ---
# MED : Notre schéma (T-Box) -> Les concepts
# INST : Nos données (A-Box) -> Les instances réelles
MED = Namespace("http://medbot.org/ontology#")
INST = Namespace("http://medbot.org/instances#")

def create_ontology_structure(g):
    """
    Définit la T-Box : Le squelette du graphe.
    C'est ici qu'on définit que 'Toux' est un symptôme.
    """
    print("Construction du Schéma (T-Box)...")
    
    # Déclaration de l'ontologie
    ontology_uri = URIRef("http://medbot.org/ontology")
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    
    # --- CLASSES (Les concepts du Use Case) ---
    classes = {
        'Disease': "Maladie",
        'Symptom': "Symptôme",
        'MedicalSpecialty': "Spécialité Médicale",
        'Department': "Département Hospitalier"
    }
    for cls, label in classes.items():
        g.add((MED[cls], RDF.type, OWL.Class))
        g.add((MED[cls], RDFS.label, Literal(label, lang='fr')))

    # --- OBJECT PROPERTIES (Les liens) ---
    # Relation : Maladie -> Symptôme
    g.add((MED.hasSymptom, RDF.type, OWL.ObjectProperty))
    g.add((MED.hasSymptom, RDFS.domain, MED.Disease))
    g.add((MED.hasSymptom, RDFS.range, MED.Symptom))
    
    # Relation : Maladie -> Spécialité (Pour l'orientation)
    g.add((MED.treatedBy, RDF.type, OWL.ObjectProperty))
    g.add((MED.treatedBy, RDFS.domain, MED.Disease))
    g.add((MED.treatedBy, RDFS.range, MED.MedicalSpecialty))
    
    # Relation : Spécialité -> Département (Pour la localisation)
    g.add((MED.belongsToDepartment, RDF.type, OWL.ObjectProperty))
    g.add((MED.belongsToDepartment, RDFS.domain, MED.MedicalSpecialty))
    g.add((MED.belongsToDepartment, RDFS.range, MED.Department))

    # --- DATA PROPERTIES (Les attributs) ---
    # Pour le triage et l'affichage
    data_props = {
        'diseaseName': XSD.string,
        'urgencyLevel': XSD.string,       # low, medium, high
        'symptomName': XSD.string,
        'severityLevel': XSD.integer,     # 1 à 7
        'departmentName': XSD.string,
        'location': XSD.string,           # Bâtiment A, etc.
        'floor': XSD.string,
        'availableSlots': XSD.integer     # Pour la gestion de flux
    }
    for prop, datatype in data_props.items():
        g.add((MED[prop], RDF.type, OWL.DatatypeProperty))
        g.add((MED[prop], RDFS.range, datatype))

    return g

def populate_knowledge_graph(g, data):
    """
    Remplit l'A-Box avec le JSON consolidé.
    Transforme chaque ligne de tes données en "Triplets RDF".
    """
    print("Injection des données (A-Box)...")
    
    # Caches pour éviter de créer 50 fois le département "Cardiology"
    dept_cache = {}
    spec_cache = {}

    # --- ÉTAPE 1 : LES DÉPARTEMENTS ---
    # Ils sont la base physique de l'hôpital
    for d in data['departments']:
        # Nettoyage URI (Ex: "Internal Medicine" -> "Dept_Internal_Medicine")
        safe_name = d['Department'].replace(' ', '_').replace('&', 'and')
        dept_uri = INST[f"Dept_{safe_name}"]
        
        g.add((dept_uri, RDF.type, MED.Department))
        g.add((dept_uri, MED.departmentName, Literal(d['Department'])))
        g.add((dept_uri, MED.location, Literal(d['Location'])))
        g.add((dept_uri, MED.floor, Literal(d['Floor'])))
        
        # Stockage en mémoire pour lier les spécialités plus tard
        dept_cache[d['Department']] = dept_uri

    # --- ÉTAPE 2 : MALADIES & SYMPTÔMES ---
    for d in data['diseases']:
        # Création URI Maladie
        dis_safe = d['disease'].replace(' ', '_').replace('(', '').replace(')', '')
        dis_uri = INST[f"Disease_{dis_safe}"]
        
        g.add((dis_uri, RDF.type, MED.Disease))
        g.add((dis_uri, MED.diseaseName, Literal(d['disease'])))
        g.add((dis_uri, MED.urgencyLevel, Literal(d['urgency'])))

        # GESTION SPÉCIALITÉ & SLOTS (Logique Métier)
        # On récupère la spécialité liée à cette maladie
        spec_name = d['specialty']
        if spec_name not in spec_cache:
            spec_uri = INST[f"Spec_{spec_name.replace(' ', '_')}"]
            g.add((spec_uri, RDF.type, MED.MedicalSpecialty))
            g.add((spec_uri, MED.specialtyName, Literal(spec_name)))
            
            # Lien Spécialité -> Département
            target_dept = d['department']
            if target_dept in dept_cache:
                dept_uri = dept_cache[target_dept]
                g.add((spec_uri, MED.belongsToDepartment, dept_uri))
                
                # Use Case : On ajoute les slots au Département (issu de la spécialité)
                # Note : C'est une simplification pour le MVP, on prend les slots de la 1ère spécialité vue
                g.add((dept_uri, MED.availableSlots, Literal(d.get('available_slots', 0))))

            spec_cache[spec_name] = spec_uri
        
        # Lien Maladie -> Spécialité
        g.add((dis_uri, MED.treatedBy, spec_cache[spec_name]))

        # GESTION SYMPTÔMES
        for s in d['symptoms']:
            sym_safe = s['name'].replace(' ', '_').replace('(', '').replace(')', '').replace("'", "")
            sym_uri = INST[f"Sym_{sym_safe}"]
            
            # Définition du symptôme
            g.add((sym_uri, RDF.type, MED.Symptom))
            g.add((sym_uri, MED.symptomName, Literal(s['name'])))
            g.add((sym_uri, MED.severityLevel, Literal(s['severity'])))
            
            # Lien Maladie -> A comme symptôme -> Symptôme
            g.add((dis_uri, MED.hasSymptom, sym_uri))

    return g

def main():
    # Configuration des chemins robustes
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '..', 'data', 'processed', 'consolidated_medical_data.json')
    ontology_dir = os.path.join(base_dir, '..', 'data', 'ontology')
    os.makedirs(ontology_dir, exist_ok=True)

    # Initialisation du Graphe
    g = Graph()
    g.bind("med", MED)
    g.bind("inst", INST)
    g.bind("owl", OWL)

    # Exécution
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        g = create_ontology_structure(g)
        g = populate_knowledge_graph(g, data)
        
        # --- Sauvegarde en format Turtle (.ttl) ---
        output_ttl = os.path.join(ontology_dir, 'medical_ontology.ttl')
        g.serialize(destination=output_ttl, format='turtle')
        print(f"Fichier Turtle généré : {output_ttl}")

        # --- Sauvegarde en format RDF/XML (.owl) ---
        output_owl = os.path.join(ontology_dir, 'medical_ontology.owl')
        g.serialize(destination=output_owl, format='xml')
        print(f"Fichier OWL (RDF/XML) généré : {output_owl}")
        
        print(f"SUCCÈS : Graphe généré avec {len(g)} triplets !")
        print(f"Fichier : {output_ttl}")
        
    except FileNotFoundError:
        print(f"ERREUR : Impossible de trouver {json_path}")
        print("Avez-vous bien lancé l'étape précédente (data_processing.py) ?")

if __name__ == "__main__":
    main()