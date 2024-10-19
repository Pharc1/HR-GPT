from flask import Blueprint, jsonify, render_template, request
from transformers import pipeline, AutoTokenizer
import os
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

# Clear any cached GPU memory
torch.cuda.empty_cache()

# Create a chatbot pipeline with mixed precision
chatbot = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.3", device="cuda", torch_dtype=torch.float16)


# Modèle d'embedding
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Tokenizer pour tronquer les contextes trop longs
tokenizer = AutoTokenizer.from_pretrained("deepset/roberta-base-squad2")

# Fonction pour obtenir les embeddings
def get_embedding(text):
    embeddings = model.encode(text)
    return np.array(embeddings)

# Fonction pour diviser un document en chunks
def chunk_text(text, chunk_size=100):
    words = text.split()
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

# Fonction pour charger et découper les fichiers .txt en chunks
def load_documents_from_folder(folder_path, chunk_size=512):
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                text = file.read()
                # Découper le texte en chunks
                document_chunks = chunk_text(text, chunk_size)
                documents.extend(document_chunks)
    return documents

# Fonction pour tronquer le contexte
def truncate_context(context, max_tokens=512):
    tokens = tokenizer.tokenize(context)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return tokenizer.convert_tokens_to_string(tokens)

# Charger les documents et découper en chunks
folder_path = 'static/documents'
documents = load_documents_from_folder(folder_path)

# Créer les embeddings pour les chunks de documents
embeddings = np.array([get_embedding(doc).flatten() for doc in documents])

# Créer un index FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
logging.info("Dimension de l'index FAISS: %d", index.d)
logging.info("Nombre d'éléments dans l'index FAISS: %d", index.ntotal)




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

    base_instructions = "Tu es un assistant très gentil qui réponds toujours avec joie aux questions, tu ne reponds que si le contexte donné te permet de repondre avec une reponse breve, sinon tu dis gentiment que tu ne peux pas répondre. "

    # Obtenir l'embedding de la question
    question_embedding = get_embedding(question).reshape(1, -1)
    logging.info("Shape of question_embedding: %s", question_embedding.shape)

    # Rechercher les documents (ou chunks) pertinents
    D, I = index.search(question_embedding, k)  # k est le nombre de chunks à récupérer
    context = " source: ".join([documents[i] for i in I[0]])  # Concaténer les chunks trouvés
    logging.info("Context trouvé: %s", context)

    # Vérifier si un contexte a été trouvé
    if context.strip() == "":
        return jsonify({"error": "Aucun contexte pertinent trouvé dans les documents."})
    context = base_instructions + " context : " + context
    # Tronquer le contexte s'il est trop long
    context = truncate_context(context)
    messages = [
    {"role": "system", "content": context},
    {"role": "user", "content": question},
    ]
    # Répondre à la question avec le contexte trouvé
    try:
        response = chatbot(messages, max_new_tokens=300)
        # Print the response
        answer = response[0]['generated_text'][-1]['content']
        logging.info("Réponse générée: %s", answer)  # Extract the generated text from the response
    except Exception as e:
        logging.error("Erreur lors de l'appel du modèle : %s", str(e))
        response = "Une erreur est survenue lors du traitement de la question."

    
    return jsonify({'answer':answer})
    