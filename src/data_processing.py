import pandas as pd
import re
import json
import os

def clean_text(text):
    """Nettoyage robuste pour Symptômes ET Maladies"""
    if pd.isna(text): return None
    text = str(text).lower()                 # Minuscules
    text = text.replace('_', ' ')            # Pas d'underscore
    text = re.sub(r'\s+', ' ', text).strip() # Pas d'espaces en trop
    
    # Correction des typos connues du dataset Kaggle
    corrections = {
        "peptic ulcer diseae": "peptic ulcer disease",
        "dimorphic hemmorhoids(piles)": "dimorphic hemmorhoids",
        "paroymsal positional vertigo": "paroxysmal positional vertigo",
        "(vertigo) paroymsal positional vertigo": "paroxysmal positional vertigo"
    }
    return corrections.get(text, text)

def process_disease_data():
    print("🔄 Chargement des données...")
    
    # --- FIX DES CHEMINS (Utilisation de chemins absolus dynamiques) ---
    # Récupère le dossier où se trouve CE script (src/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construit le chemin vers data/raw en remontant d'un cran
    raw_path = os.path.join(current_dir, '..', 'data', 'raw')
    processed_path = os.path.join(current_dir, '..', 'data', 'processed')

    # Création du dossier processed s'il n'existe pas
    os.makedirs(processed_path, exist_ok=True)

    try:
        df_diseases = pd.read_csv(os.path.join(raw_path, 'dataset.csv'))
        df_severity = pd.read_csv(os.path.join(raw_path, 'Symptom-severity.csv'))
        df_specialties = pd.read_csv(os.path.join(raw_path, 'medical_specialties.csv'))
        df_departments = pd.read_csv(os.path.join(raw_path, 'departments.csv'))
    except FileNotFoundError as e:
        print(f"❌ ERREUR CRITIQUE : Fichier introuvable.\nLe script cherche ici : {raw_path}\nVérifie que tes fichiers CSV sont bien dans le dossier 'data/raw'.")
        raise e

    # 1. NETTOYAGE PRÉALABLE
    print("🧹 Normalisation des noms...")
    for df in [df_diseases, df_specialties]:
        df['Disease'] = df['Disease'].apply(clean_text)
    
    df_severity['Symptom'] = df_severity['Symptom'].apply(clean_text)
    severity_map = dict(zip(df_severity['Symptom'], df_severity['weight']))

    # 2. AGRÉGATION
    diseases_data = []
    unique_diseases = df_diseases['Disease'].unique()

    print(f"⚙️ Traitement de {len(unique_diseases)} maladies uniques...")

    for disease_name in unique_diseases:
        disease_rows = df_diseases[df_diseases['Disease'] == disease_name]
        
        all_symptoms = set()
        for col in df_diseases.columns[1:]:
            symptoms = disease_rows[col].dropna().apply(clean_text).tolist()
            all_symptoms.update(symptoms)
        
        formatted_symptoms = []
        for s in all_symptoms:
            if s:
                formatted_symptoms.append({
                    'name': s,
                    'severity': int(severity_map.get(s, 3))
                })

        spec_info = df_specialties[df_specialties['Disease'] == disease_name]
        
        if not spec_info.empty:
            row = spec_info.iloc[0]
            diseases_data.append({
                'disease': disease_name,
                'symptoms': formatted_symptoms,
                'specialty': row['Specialty'],
                'department': row['Department'],
                'urgency': row['Urgency'],
                'available_slots': int(row['AvailableSlots'])
            })
        else:
            print(f"⚠️ Pas de spécialité pour : '{disease_name}'")

    # 3. SAUVEGARDE
    output_file = os.path.join(processed_path, 'consolidated_medical_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'diseases': diseases_data,
            'departments': df_departments.to_dict('records')
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ SUCCÈS : Données sauvegardées dans {output_file}")
    print(f"   Total maladies traitées : {len(diseases_data)}")
    return diseases_data

if __name__ == "__main__":
    process_disease_data()