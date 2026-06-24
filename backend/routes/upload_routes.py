import os
from flask import Blueprint, request, jsonify

from services.document_loader import load_pdf_text
from services.chunking import chunk_pages
from services.vector_store import add_chunks_to_vector_store

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = "uploads"


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported right now"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    pages = load_pdf_text(file_path)
    chunks = chunk_pages(pages, file.filename)

    chunks_stored = add_chunks_to_vector_store(chunks)

    return jsonify({
        "message": "File uploaded, chunked, embedded, and stored in ChromaDB successfully",
        "filename": file.filename,
        "pages_extracted": len(pages),
        "chunks_created": len(chunks),
        "chunks_stored": chunks_stored,
        "first_chunk_metadata": chunks[0]["metadata"] if chunks else {}
    })