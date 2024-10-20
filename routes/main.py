from flask import Blueprint, jsonify, render_template, request, Response
import numpy as np
import logging
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

# Configuration du logging pour le suivi des informations et des erreurs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création d'un blueprint Flask pour le module principal
main = Blueprint('main', __name__)

# Initialisation du client OpenAI
client = OpenAI()

# Définition du chemin pour la base de données Chroma
CHROMA_PATH = "chroma"

def chunk_text(documents, chunk_size, chunk_overlap):
    """Découpe les documents en morceaux de texte selon les paramètres spécifiés.

    Args:
        documents (list): Liste des documents à découper.
        chunk_size (int): Taille maximale de chaque morceau.
        chunk_overlap (int): Nombre de caractères à chevaucher entre les morceaux.

    Returns:
        list: Liste des morceaux de texte découpés.
    """
    # Crée le text splitter avec les paramètres spécifiés
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    logging.info("Découpé %d documents en %d morceaux", len(documents), len(chunks))
    return chunks

def load_documents_from_folder(folder_path, chunk_size=512):
    """Charge les fichiers .txt depuis un dossier et les découpe en morceaux.

    Args:
        folder_path (str): Chemin du dossier contenant les fichiers texte.
        chunk_size (int): Taille des morceaux de texte.

    Returns:
        list: Liste des morceaux de texte découpés.
    """
    try:
        loader = DirectoryLoader(folder_path, glob="*.txt")
        documents = loader.load()
        # Découpe les documents en morceaux
        documents = chunk_text(documents, chunk_size, 50)

        # Log l'information sur le dixième document pour avoir un aperçu 
        if len(documents) > 10:  # Vérifie qu'il y a au moins 10 documents
            logging.info("Contenu du 10ème document: %s", documents[10].page_content)
            logging.info("Métadonnées du 10ème document: %s", documents[10].metadata)
        
        return documents

    except Exception as e:
        logging.error("Erreur lors du chargement des documents: %s", str(e))
        return []

# Charger les documents et découper en morceaux
folder_path = 'static/documents'
documents = load_documents_from_folder(folder_path)

# Création des embeddings pour les morceaux de documents
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialisation de la base de données Chroma avec les documents et les embeddings
try:
    db = Chroma.from_documents(
        documents, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
    )

    if db.persist():
        logging.info("Sauvegardé %s morceaux dans %s", len(documents), CHROMA_PATH)

except Exception as e:
    logging.error("Erreur lors de l'initialisation de Chroma: %s", str(e))


@main.route("/")
def home():
    """Affiche la page d'accueil."""
    return render_template('index.html')

@main.route("/about")
def about():
    """Affiche la page à propos."""
    return render_template('about.html')

@main.route('/ask', methods=['GET', 'POST'])
def ask():
    """Traite les demandes de questions de l'utilisateur.

    Returns:
        Response: Réponse générée par l'API OpenAI ou un message d'erreur.
    """
    k = 5  # Nombre d'extraits à obtenir
    question = ""

    # Traitement de la requête POST ou GET
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

    # Cherchez les résultats
    try:
        results = db.similarity_search_with_relevance_scores(question, k=k)

        context_set = set()
        context = []

        # Parcourez les résultats et assurez-vous d'ajouter uniquement des extraits uniques
        for doc, _score in results:
            # Vérifiez si le contenu n'est pas déjà dans l'ensemble
            if doc.page_content not in context_set:
                context_set.add(doc.page_content)
                context.append(doc.page_content)

                # Arrêtez l'ajout si vous avez atteint le nombre souhaité d'extraits différents
                if len(context) >= k:
                    break

        context = "\n\n---\n\n".join(context)  # Modifie pour utiliser une nouvelle ligne
        logging.info("Contexte trouvé: %s", context)

        if context.strip() == "":
            return jsonify({"error": "Aucun contexte pertinent trouvé dans les documents."}), 404

        # Préparez les messages pour l'API OpenAI
        context = base_instructions + " connaissances : " + context
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": question},
        ]

        def generate():
            """Génère les réponses de l'API OpenAI en streaming."""
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

        # Envoyez une réponse appropriée avec des en-têtes pour éviter le cache
        return Response(generate(), content_type="text/plain", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    except Exception as e:
        logging.error("Erreur lors de la recherche de similarité : %s", str(e))
        return jsonify({"error": "Erreur lors de la recherche de similarité."}), 500
