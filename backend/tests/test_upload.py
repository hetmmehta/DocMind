import io

import pytest
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai._common import GoogleGenerativeAIError

from conftest import make_pdf
from routes import upload_routes
from services.errors import QUOTA_ERROR_MESSAGE


@pytest.fixture
def stored_chunks(monkeypatch):
    """
    Replace the vector store call so uploads never call Gemini.
    """
    calls = []

    def fake_replace(filename, chunks):
        calls.append((filename, chunks))
        return len(chunks)

    monkeypatch.setattr(upload_routes, "replace_document_chunks", fake_replace)
    return calls


def _upload(client, data, filename):
    return client.post(
        "/upload",
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def test_upload_valid_pdf(client, upload_dir, stored_chunks):
    response = _upload(client, make_pdf("Hello DocMind"), "my report (1).pdf")

    assert response.status_code == 200
    body = response.get_json()
    assert body["filename"] == "my_report_1.pdf"
    assert body["chunks_stored"] == 1
    assert body["first_chunk_metadata"] == {"filename": "my_report_1.pdf", "page_number": 1, "chunk_index": 0}
    assert "Hello DocMind" in stored_chunks[0][1][0]["text"]

    saved = list(upload_dir.iterdir())
    assert len(saved) == 1
    prefix, _, name = saved[0].name.partition("_")
    assert len(prefix) == 32 and name == "my_report_1.pdf"


def test_reupload_replaces_previous_stored_file(client, upload_dir, stored_chunks):
    _upload(client, make_pdf("first"), "doc.pdf")
    _upload(client, make_pdf("second"), "doc.pdf")

    assert len(list(upload_dir.iterdir())) == 1
    assert [call[0] for call in stored_chunks] == ["doc.pdf", "doc.pdf"]


def test_upload_rejects_non_pdf_extension(client, upload_dir, stored_chunks):
    response = _upload(client, b"just some text", "notes.txt")

    assert response.status_code == 400
    assert "PDF" in response.get_json()["error"]
    assert list(upload_dir.iterdir()) == []
    assert stored_chunks == []


def test_upload_rejects_bad_magic_bytes(client, upload_dir, stored_chunks):
    response = _upload(client, b"MZ\x90\x00 definitely not a pdf", "invoice.pdf")

    assert response.status_code == 400
    assert response.get_json()["error"] == "The uploaded file is not a valid PDF"
    assert list(upload_dir.iterdir()) == []
    assert stored_chunks == []


@pytest.mark.parametrize("filename", [
    "../../etc/evil.pdf",
    "..\\..\\windows\\evil.pdf",
    "/tmp/evil.pdf",
])
def test_upload_rejects_path_traversal_filenames(client, upload_dir, stored_chunks, filename):
    response = _upload(client, make_pdf(), filename)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid filename"
    assert list(upload_dir.iterdir()) == []
    assert list(upload_dir.parent.glob("*.pdf")) == []


def test_upload_rejects_oversized_file(client, upload_dir, stored_chunks):
    too_big = make_pdf() + b"0" * (1024 * 1024)

    response = _upload(client, too_big, "big.pdf")

    assert response.status_code == 413
    assert "too large" in response.get_json()["error"]
    assert list(upload_dir.iterdir()) == []


def test_upload_rejects_unparseable_pdf(client, upload_dir, stored_chunks):
    response = _upload(client, b"%PDF-1.4\nthis is not really a pdf", "broken.pdf")

    assert response.status_code in (400, 422)
    assert "error" in response.get_json()
    assert list(upload_dir.iterdir()) == []
    assert stored_chunks == []


def test_upload_quota_error_returns_clean_429(client, upload_dir, monkeypatch):
    def quota_exceeded(filename, chunks):
        # This mirrors how langchain-google-genai wraps the Google error during embedding.
        try:
            raise ResourceExhausted("Quota exceeded for embed_content")
        except ResourceExhausted as e:
            raise GoogleGenerativeAIError("Error embedding content") from e

    monkeypatch.setattr(upload_routes, "replace_document_chunks", quota_exceeded)

    response = _upload(client, make_pdf(), "doc.pdf")

    assert response.status_code == 429
    assert response.get_json() == {"error": QUOTA_ERROR_MESSAGE}
    assert list(upload_dir.iterdir()) == []


def test_upload_unexpected_error_is_not_leaked(client, upload_dir, monkeypatch):
    def boom(filename, chunks):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(upload_routes, "replace_document_chunks", boom)

    response = _upload(client, make_pdf(), "doc.pdf")

    assert response.status_code == 500
    assert "secret internal detail" not in response.get_data(as_text=True)
    assert list(upload_dir.iterdir()) == []
