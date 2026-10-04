import os
import uuid

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DB_DIR

COLLECTION_NAME = "docmind_collection"


def get_embedding_model():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )


def get_vector_store(with_embeddings=True):
    """
    Open the persistent Chroma collection.
    Listing and deleting documents does not need embeddings, so those
    callers can skip creating the Gemini embedding client.
    """
    embeddings = get_embedding_model() if with_embeddings else None

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )


def _get_chunk_ids(vector_store, filename):
    result = vector_store.get(where={"filename": filename}, include=[])
    return result.get("ids", [])


def replace_document_chunks(filename, chunks):
    """
    Store the chunks for a document, replacing any chunks previously stored
    for the same filename. New chunks are added before the old ones are
    removed so a failed upload (e.g. quota error) never loses the old copy.
    """
    vector_store = get_vector_store()

    old_ids = _get_chunk_ids(vector_store, filename)

    upload_id = uuid.uuid4().hex
    documents = []
    ids = []

    for chunk in chunks:
        metadata = chunk["metadata"]

        doc = Document(
            page_content=chunk["text"],
            metadata=metadata
        )

        documents.append(doc)

        doc_id = f"{upload_id}_page_{metadata['page_number']}_chunk_{metadata['chunk_index']}"
        ids.append(doc_id)

    if documents:
        vector_store.add_documents(documents=documents, ids=ids)

    if old_ids:
        vector_store.delete(ids=old_ids)

    return len(documents)


def list_documents():
    """
    Return every ingested document with its chunk and page counts.
    """
    vector_store = get_vector_store(with_embeddings=False)
    result = vector_store.get(include=["metadatas"])

    documents = {}

    for metadata in result.get("metadatas") or []:
        if not metadata:
            continue

        filename = metadata.get("filename")
        entry = documents.setdefault(filename, {"filename": filename, "chunks": 0, "pages": set()})
        entry["chunks"] += 1
        entry["pages"].add(metadata.get("page_number"))

    return [
        {"filename": entry["filename"], "chunks": entry["chunks"], "pages": len(entry["pages"])}
        for entry in sorted(documents.values(), key=lambda item: str(item["filename"]).lower())
    ]


def delete_document(filename):
    """
    Delete all chunks for a document. Returns how many chunks were removed.
    """
    vector_store = get_vector_store(with_embeddings=False)
    ids = _get_chunk_ids(vector_store, filename)

    if ids:
        vector_store.delete(ids=ids)

    return len(ids)
