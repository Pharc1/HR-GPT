import os
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader

# Configure logging
logging.basicConfig(level=logging.INFO)

client = chromadb.HttpClient(host='https://chroma-482049242144.us-central1.run.app', port=8000)
logging.info("heartbeat %d", client.heartbeat())

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
        if len(documents) > 1:  # Vérifie qu'il y a au moins 10 documents
            logging.info("Contenu du 10ème document: %s", documents[1].page_content)
            logging.info("Métadonnées du 10ème document: %s", documents[1].metadata)
        
        return documents

    except Exception as e:
        logging.error("Erreur lors du chargement des documents: %s", str(e))
        return []

# Charger les documents et découper en morceaux
folder_path = 'app/static/documents'
documents = load_documents_from_folder(folder_path)


# Création d'une fonction d'embedding
embeddings_model = embedding_functions.OpenAIEmbeddingFunction(model_name="text-embedding-3-small", api_key=os.getenv('OPENAI_API_KEY'))

# Création d'une collection pour stocker les documents
collection = client.get_or_create_collection(name ="Documents", embedding_function=embeddings_model)

# Ajouter les documents avec leurs embeddings
try:
    for i, doc in enumerate(documents):
        # Génération d'un ID unique pour chaque document
        doc_id = f"doc_{i}"
        
        # Ajoutez le document à la collection
        collection.add(
            documents=[doc.page_content],
            metadatas=[doc.metadata],
            ids=[doc_id]
        )

    # Persister la base de données
    logging.info("Sauvegardé %d morceaux dans la base de donnée", len(documents))

except Exception as e:
    logging.error("Erreur lors de l'initialisation de Chroma: %s", str(e))

results = collection.query(
    query_texts=["This is a query document about hawaii"], # Chroma will embed this for you
    n_results=3 # how many results to return
)

context = "/n/n----/n/n".join(doc for doc  in results['documents'][0])
print("context:",context)
print("results:", results)
