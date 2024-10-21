#!/bin/bash

# vérifier si Chroma répond
wait_for_chroma() {
    until python -c "import chromadb; chroma_client = chromadb.HttpClient(host='chroma', port=8000); chroma_client.heartbeat()"; do
        echo "Attente que Chroma soit opérationnel..."
        sleep 2
    done
    echo "Chroma est opérationnel !"
}

# Attendre que Chroma soit opérationnel
wait_for_chroma

# Exécuter init.py
echo "Lancement de init.py..."
python init.py

# Lancer l'application Flask
echo "Démarrage de l'application Flask..."
exec python app.py
