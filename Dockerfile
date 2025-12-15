# Utilise une image de base Python légère
FROM python:3.11-slim

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Copie les dépendances et les installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste du code
COPY app /app/app

# Définit le point d'entrée pour l'application
CMD ["python", "app/main.py"]