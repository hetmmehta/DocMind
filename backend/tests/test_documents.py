import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from routes import document_routes
from services import vector_store


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    """
    A real on-disk Chroma collection with fake (offline) embeddings.
    """
    monkeypatch.setattr(vector_store, "CHROMA_DB_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr(vector_store, "get_embedding_model", lambda: DeterministicFakeEmbedding(size=16))


def _chunks(filename, count):
    return [
        {
            "text": f"{filename} chunk {i}",
            "metadata": {"filename": filename, "page_number": i // 2 + 1, "chunk_index": i % 2},
        }
        for i in range(count)
    ]


def test_reupload_with_fewer_chunks_leaves_no_stale_chunks(local_store):
    vector_store.replace_document_chunks("a.pdf", _chunks("a.pdf", 6))
    vector_store.replace_document_chunks("b.pdf", _chunks("b.pdf", 2))

    vector_store.replace_document_chunks("a.pdf", _chunks("a.pdf", 2))

    assert vector_store.list_documents() == [
        {"filename": "a.pdf", "chunks": 2, "pages": 1},
        {"filename": "b.pdf", "chunks": 2, "pages": 1},
    ]


def test_delete_document_removes_only_that_document(local_store):
    vector_store.replace_document_chunks("a.pdf", _chunks("a.pdf", 3))
    vector_store.replace_document_chunks("b.pdf", _chunks("b.pdf", 2))

    assert vector_store.delete_document("a.pdf") == 3
    assert vector_store.delete_document("a.pdf") == 0
    assert [doc["filename"] for doc in vector_store.list_documents()] == ["b.pdf"]


def test_list_documents_endpoint(client, monkeypatch):
    monkeypatch.setattr(
        document_routes, "list_documents",
        lambda: [{"filename": "Profile.pdf", "chunks": 4, "pages": 2}],
    )

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.get_json() == {"documents": [{"filename": "Profile.pdf", "chunks": 4, "pages": 2}]}


def test_delete_document_endpoint_removes_stored_file(client, upload_dir, monkeypatch):
    stored = upload_dir / ("0" * 32 + "_Profile.pdf")
    stored.write_bytes(b"%PDF-1.4")
    other = upload_dir / ("1" * 32 + "_Other.pdf")
    other.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(document_routes, "delete_document", lambda filename: 4)

    response = client.delete("/documents/Profile.pdf")

    assert response.status_code == 200
    assert response.get_json()["chunks_deleted"] == 4
    assert not stored.exists()
    assert other.exists()


def test_delete_unknown_document_returns_404(client, monkeypatch):
    monkeypatch.setattr(document_routes, "delete_document", lambda filename: 0)

    response = client.delete("/documents/missing.pdf")

    assert response.status_code == 404
