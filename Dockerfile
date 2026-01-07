# Utilise une image de base Python légère
FROM python:3.11-slim

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie les dépendances et les installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharge les modèles spaCy pour NLP (français et anglais)
RUN python -m spacy download fr_core_news_sm
RUN python -m spacy download en_core_web_sm

# Copie le reste du code
COPY src /app/src
COPY app /app/app
COPY data /app/data

# Définit le point d'entrée pour l'application Streamlit
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]