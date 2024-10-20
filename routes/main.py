from flask import Blueprint, jsonify, render_template, request, Response
import os
import faiss
import numpy as np
import logging
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader


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
    

def chunk_text(documents, chunk_size=100, chunk_overlap=20):
    # Crée le text splitter avec les paramètres spécifiés
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    logging.info("split %d documents into %d chunks", len(documents), len(chunks))
    return chunks

# Fonction pour charger et découper les fichiers .txt en chunks
def load_documents_from_folder(folder_path, chunk_size=512):
    loader = DirectoryLoader(folder_path, glob = "*.txt")
    documents = loader.load()
    documents = chunk_text(documents, 500, 100)
    document = documents[10]
    logging.info("content of 10th document: %s", document.page_content)
    logging.info("document 10th metadata: %s", document.metadata)
    return documents

# Charger les documents et découper en chunks
folder_path = 'static/documents'
documents = load_documents_from_folder(folder_path)

# Créer les embeddings pour les chunks de documents
embeddings = np.array([get_embedding(doc.page_content).flatten() for doc in documents])

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

    base_instructions = """
    tu es Jovia est un assistant bienveillant qui vouvoie toujours et répond avec joie et émojis. 
    tu fournit uniquement des réponses basées sur ses connaissances. 
    Si une question dépasse tes connaissances, tu l'indique gentiment. 
    Lorsqu'une adresse mail est donnée, Jovia renvoie un lien mailto avec un sujet et un corps appropriés attention les saut de ligne sont %0A%0A: <a href="mailto:exemple@exemple.com?subject=Sujet pertinent&body=Bonjour,%0A%0AVoici les informations demandées.">exemple@exemple.com</a>
    elle indique gentiment que le lien est cliquable avec un mail préparé.
    """
    question_embedding = get_embedding(question).reshape(1, -1)
    logging.info("Shape of question_embedding: %s", question_embedding.shape)

    D, I = index.search(question_embedding, k)
    context = " ".join([documents[i].page_content for i in I[0]])
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


   