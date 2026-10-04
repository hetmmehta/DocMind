import logging
import os
import uuid

from flask import Blueprint, current_app, request, jsonify
from pypdf.errors import PdfReadError
from werkzeug.utils import secure_filename

from services.document_loader import load_pdf_text
from services.chunking import chunk_pages
from services.errors import QUOTA_ERROR_MESSAGE, is_quota_error
from services.storage import remove_stored_files
from services.vector_store import replace_document_chunks

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)

# A valid PDF has its "%PDF-" header within the first 1024 bytes.
PDF_MAGIC = b"%PDF-"
PDF_HEADER_WINDOW = 1024


def _is_pdf(file_storage):
    head = file_storage.stream.read(PDF_HEADER_WINDOW)
    file_storage.stream.seek(0)
    return PDF_MAGIC in head


def _remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


@upload_bp.app_errorhandler(413)
def file_too_large(_error):
    max_mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return jsonify({
        "error": f"File is too large. The maximum upload size is {max_mb} MB."
    }), 413


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Browsers only ever send a bare filename, so anything with a path in it is suspicious.
    if "/" in file.filename or "\\" in file.filename:
        return jsonify({"error": "Invalid filename"}), 400

    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported right now"}), 400

    if not _is_pdf(file):
        return jsonify({"error": "The uploaded file is not a valid PDF"}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    # Prefix with a random id so uploads never overwrite each other on disk.
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(upload_folder, stored_name)
    file.save(file_path)

    try:
        pages = load_pdf_text(file_path)

        if not pages:
            _remove_file(file_path)
            return jsonify({
                "error": "No extractable text found in this PDF. Scanned PDFs are not supported yet."
            }), 422

        chunks = chunk_pages(pages, filename)
        chunks_stored = replace_document_chunks(filename, chunks)

    except PdfReadError:
        logger.warning("Could not parse uploaded PDF %s", filename, exc_info=True)
        _remove_file(file_path)
        return jsonify({"error": "The uploaded file could not be read as a PDF"}), 400

    except Exception as e:
        _remove_file(file_path)

        if is_quota_error(e):
            logger.warning("Gemini quota exceeded while embedding %s: %s", filename, e)
            return jsonify({"error": QUOTA_ERROR_MESSAGE}), 429

        logger.exception("Failed to ingest %s", filename)
        return jsonify({
            "error": "Something went wrong while processing the document."
        }), 500

    # Re-uploading a document replaces it, so drop older copies on disk too.
    remove_stored_files(upload_folder, filename, keep=stored_name)

    return jsonify({
        "message": "File uploaded, chunked, embedded, and stored in ChromaDB successfully",
        "filename": filename,
        "pages_extracted": len(pages),
        "chunks_created": len(chunks),
        "chunks_stored": chunks_stored,
        "first_chunk_metadata": chunks[0]["metadata"] if chunks else {}
    })
