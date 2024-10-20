from flask import Blueprint, jsonify, render_template, request, Response
import os
import faiss
import numpy as np
import logging
from openai import OpenAI


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

# Initialisation du client OpenAI
client = OpenAI()


# Fonction pour obtenir l'embedding de la question
def get_embedding(text):
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        return np.array(embedding)
    except Exception as e:
        logging.error("Erreur lors de l'obtention de l'embedding : %s", str(e))
        return None

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

@main.route('/ask', methods=['GET', 'POST'])
def ask():
    k = 5
    question = ""
    if request.method == 'POST':
        data = request.json
        question = data.get('question')
    elif request.method == 'GET':
        question = request.args.get('question')

    # Vérifiez que la question a été fournie
    if not question:
        return jsonify({"error": "Aucune question fournie."}), 400

    base_instructions = "Tu es un assistant très gentil qui vouvoie répond toujours avec joie et bienveillance aux questions et des emojies. Tu dois toujours répondre uniquement en fonction de tes connaissances, si une question n'est pas liée à tes conaissances ou si la reponse n'est pas dans les connaissances tu ne réponds pas"
    question_embedding = get_embedding(question).reshape(1, -1)
    logging.info("Shape of question_embedding: %s", question_embedding.shape)

    D, I = index.search(question_embedding, k)
    context = " source: ".join([documents[i] for i in I[0]])
    logging.info("Context trouvé: %s", context)

    if context.strip() == "":
        return jsonify({"error": "Aucun contexte pertinent trouvé dans les documents."}), 404

    context = base_instructions + " coonaissances : " + context
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": question},
    ]

    def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logging.error("Erreur lors de l'appel du modèle : %s", str(e))
            yield f"data: Une erreur est survenue lors du traitement de la question.\n\n"

    # Send an appropriate response with headers to prevent caching
    return Response(generate(), content_type="text/plain", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


   