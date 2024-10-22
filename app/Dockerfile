# app/Dockerfile

FROM python:3.9-slim

# Met à jour les paquets et installe les dépendances nécessaires
RUN apt-get update && \
    apt-get install -y curl libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier requirements.txt et installe les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le script start.sh et donne les permissions d'exécution
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Copie le reste des fichiers de l'application
COPY . .

# Expose le port sur lequel l'application écoute
EXPOSE 5000

# Définit le point d'entrée pour le conteneur
ENTRYPOINT ["./start.sh"]
