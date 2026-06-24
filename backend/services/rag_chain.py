import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from services.vector_store import get_vector_store

load_dotenv()


def ask_question(question):
    vector_store = get_vector_store()

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}
    )

    relevant_docs = retriever.invoke(question)

    context = "\n\n".join([
        f"Source: {doc.metadata.get('filename')}, page {doc.metadata.get('page_number')}\n{doc.page_content}"
        for doc in relevant_docs
    ])

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2
    )

    prompt = f"""
You are DocMind, a helpful AI assistant that answers questions using only the provided document context.

Rules:
1. Answer only from the context below.
2. If the answer is not in the context, say: "I could not find that information in the uploaded documents."
3. Be clear and concise.
4. Include citations using the filename and page number, for example: (Profile.pdf, page 1).
5. If multiple sources support the answer, cite the most relevant ones only.

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    sources = []
    for doc in relevant_docs:
        sources.append({
            "filename": doc.metadata.get("filename"),
            "page_number": doc.metadata.get("page_number"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "preview": doc.page_content[:250]
        })

    return {
        "answer": response.content,
        "sources": sources
    }