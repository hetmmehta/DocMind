import logging

from flask import Flask, jsonify
from flask_cors import CORS

import config
from routes.upload_routes import upload_bp
from routes.chat_routes import chat_bp
from routes.document_routes import document_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


def create_app(overrides=None):
    app = Flask(__name__)

    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

    if overrides:
        app.config.update(overrides)

    CORS(app, origins=config.CORS_ORIGINS)

    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(document_bp)

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "message": "DocMind backend is running"
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG, port=config.PORT)
