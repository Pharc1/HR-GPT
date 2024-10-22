from flask import Blueprint, jsonify, render_template, request, Response
import logging
from openai import OpenAI
from chromadb.utils import embedding_functions
import os
import chromadb

# Configuration du logging pour le suivi des informations et des erreurs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création d'un blueprint Flask pour le module principal
main = Blueprint('main', __name__)

# Initialisation du client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Définition du chemin pour la base de données Chroma
# Configuration du client Chroma
chroma_host = os.getenv('CHROMA_DB_HOST', 'chroma')  
chroma_port = os.getenv('CHROMA_DB_PORT', 8000) 
chroma_client = chromadb.HttpClient(host="https://chroma-482049242144.us-central1.run.app", port=chroma_port)
embeddings_model = embedding_functions.OpenAIEmbeddingFunction(model_name="text-embedding-3-small", api_key=os.getenv('OPENAI_API_KEY'))

@main.route("/")
def home():
    """Affiche la page d'accueil."""
    return render_template('index.html')

@main.route("/about")
def about():
    """Affiche la page à propos."""
    return render_template('about.html')

@main.route('/health')
def health_check():
    return "Healthy", 200

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
        collection = chroma_client.get_or_create_collection(name ="Documents", embedding_function=embeddings_model)
        results = collection.query(
            query_texts=[question], # Chroma will embed this for you
            n_results=5 # how many results to return
        )

        context = "/n/n----/n/n".join(doc for doc  in results['documents'][0])
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
