# Utiliser une image de base Python
FROM python:3.9

# Définir le répertoire de travail
WORKDIR /chromadb

# Copier le script d'initialisation et les fichiers nécessaires
COPY . . 

# Installer les dépendances nécessaires
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port de Chroma
EXPOSE 8001

# Exécuter le script d'initialisation
CMD ["python", "init.py"]
