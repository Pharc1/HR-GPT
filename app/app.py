from flask import Flask
from routes.main import main
from routes.documents import documents
app = Flask(__name__)


app.register_blueprint(main)
app.register_blueprint(documents)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
