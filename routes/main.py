from flask import Blueprint, jsonify, render_template, request
from transformers import pipeline


main = Blueprint('main', __name__)

nlp = pipeline("question-answering", model="deepset/roberta-base-squad2")



@main.route("/")
def home():
    return render_template('index.html')

@main.route("/about")
def about():
    return render_template('about.html')


@main.route("/ask", methods= ["POST"])
def ask():
    data = request.json
    question = data.get('question')
    context = "pharci est le plus beau"

    if not question or not context:
        return jsonify({"error": "Question and context are required."}), 400

    # Utilisation du modèle pour obtenir la réponse
    result = nlp({'question': question, 'context': context})
    print(result)
    return jsonify(result)
