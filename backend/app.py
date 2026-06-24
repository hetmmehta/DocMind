from flask import Flask, jsonify
from flask_cors import CORS

from routes.upload_routes import upload_bp
from routes.chat_routes import chat_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(upload_bp)
app.register_blueprint(chat_bp)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "DocMind backend is running"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)