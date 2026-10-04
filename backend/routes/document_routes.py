import logging

from flask import Blueprint, current_app, jsonify

from services.storage import remove_stored_files
from services.vector_store import delete_document, list_documents

logger = logging.getLogger(__name__)

document_bp = Blueprint("documents", __name__)


@document_bp.route("/documents", methods=["GET"])
def get_documents():
    try:
        documents = list_documents()
    except Exception:
        logger.exception("Failed to list documents")
        return jsonify({"error": "Could not load the document list."}), 500

    return jsonify({"documents": documents})


@document_bp.route("/documents/<path:filename>", methods=["DELETE"])
def remove_document(filename):
    try:
        chunks_deleted = delete_document(filename)
    except Exception:
        logger.exception("Failed to delete %s", filename)
        return jsonify({"error": "Could not delete the document."}), 500

    if chunks_deleted == 0:
        return jsonify({"error": "Document not found"}), 404

    remove_stored_files(current_app.config["UPLOAD_FOLDER"], filename)

    return jsonify({
        "message": "Document deleted",
        "filename": filename,
        "chunks_deleted": chunks_deleted
    })
