from flask import Blueprint, jsonify, render_template, request
from transformers import pipeline, AutoTokenizer, AutoModel
import PyPDF2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer


main = Blueprint('main', __name__)

nlp = pipeline("question-answering", model="deepset/roberta-base-squad2")

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Fonction pour obtenir les embeddings
def get_embedding(text):
    embeddings = model.encode(text)
    return np.array(embeddings)

# Fonction pour charger les fichiers .txt
def load_documents_from_folder(folder_path):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                documents.append(file.read())
    return documents



# Charger les documents
folder_path = 'static/documents'  # Remplace par le chemin de ton dossier
documents = load_documents_from_folder(folder_path)

# Créer les embeddings pour les documents
embeddings = np.array([get_embedding(doc).flatten() for doc in documents])

# Créer un index FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
print("Dimension de l'index FAISS:", index.d)
print("Nombre d'éléments dans l'index FAISS:", index.ntotal)  # Devrait être égal au nombre de documents chargés



@main.route("/")
def home():
    return render_template('index.html')

@main.route("/about")
def about():
    return render_template('about.html')


@main.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    k = 5

    # Obtenir l'embedding de la question
    question_embedding = get_embedding(question).reshape(1, -1)
    print("Shape of question_embedding:", question_embedding.shape)

    # Rechercher les documents pertinents
    D, I = index.search(question_embedding, k)  # k est le nombre de documents à récupérer
    context = " ".join([documents[i] for i in I[0] if i < len(documents)])

    # Répondre à la question avec le contexte trouvé
    result = nlp({'question': question, 'context': context})
    return jsonify(result)