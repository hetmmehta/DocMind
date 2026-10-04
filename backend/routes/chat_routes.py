import logging

from flask import Blueprint, request, jsonify

from services.errors import QUOTA_ERROR_MESSAGE, is_quota_error
from services.rag_chain import ask_question

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400

    question = data["question"]

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Question is required"}), 400

    # Optional: limit retrieval to a single uploaded document.
    document = data.get("document") or None

    if document is not None and not isinstance(document, str):
        return jsonify({"error": "document must be a filename string"}), 400

    try:
        result = ask_question(question.strip(), document=document)
        return jsonify(result)

    except Exception as e:
        if is_quota_error(e):
            logger.warning("Gemini quota exceeded while answering a question: %s", e)
            return jsonify({"error": QUOTA_ERROR_MESSAGE}), 429

        logger.exception("Failed to generate an answer")
        return jsonify({
            "error": "Something went wrong while generating the answer."
        }), 500
