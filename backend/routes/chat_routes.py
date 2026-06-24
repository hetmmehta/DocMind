from flask import Blueprint, request, jsonify
from services.rag_chain import ask_question

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400

    question = data["question"]

    try:
        result = ask_question(question)
        return jsonify(result)

    except Exception as e:
        error_message = str(e)

        if "429" in error_message or "quota" in error_message.lower() or "ResourceExhausted" in error_message:
            return jsonify({
                "error": "Gemini API quota exceeded. Please try again later or switch to another available model/API key."
            }), 429

        return jsonify({
            "error": "Something went wrong while generating the answer.",
            "details": error_message
        }), 500