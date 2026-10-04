import os

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


def get_vector_store():
    embeddings = get_embedding_model()

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )


def add_chunks_to_vector_store(chunks):
    vector_store = get_vector_store()

    documents = []
    ids = []

    for i, chunk in enumerate(chunks):
        metadata = chunk["metadata"]

        doc = Document(
            page_content=chunk["text"],
            metadata=metadata
        )

        documents.append(doc)

        doc_id = f"{metadata['filename']}_page_{metadata['page_number']}_chunk_{metadata['chunk_index']}_{i}"
        ids.append(doc_id)

    vector_store.add_documents(documents=documents, ids=ids)

    return len(documents)