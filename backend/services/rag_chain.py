import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from services.vector_store import get_vector_store

TOP_K = 3

NOT_FOUND_MESSAGE = "I could not find that information in the uploaded documents."

SYSTEM_PROMPT = f"""You are DocMind, a helpful AI assistant that answers questions using only the provided document context.

Rules:
1. Answer only from the context below.
2. If the answer is not in the context, say: "{NOT_FOUND_MESSAGE}"
3. Be clear and concise.
4. Include citations using the filename and page number, for example: (Profile.pdf, page 1).
5. If multiple sources support the answer, cite the most relevant ones only."""

HUMAN_PROMPT = """Context:
{context}

Question:
{question}

Answer:"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT),
])


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2
    )


def get_retriever(document=None):
    """
    Top-k similarity retriever over the Chroma collection.
    If a document filename is given, retrieval is limited to that document.
    """
    search_kwargs = {"k": TOP_K}

    if document:
        search_kwargs["filter"] = {"filename": document}

    return get_vector_store().as_retriever(search_kwargs=search_kwargs)


def format_docs(docs):
    return "\n\n".join([
        f"Source: {doc.metadata.get('filename')}, page {doc.metadata.get('page_number')}\n{doc.page_content}"
        for doc in docs
    ])


def build_rag_chain(retriever, llm):
    """
    LCEL retrieval chain:

        question -> retriever -> format docs -> prompt -> Gemini -> string

    The retrieved documents are kept in the output so the API can return
    structured sources alongside the answer.
    """
    answer_chain = (
        RunnablePassthrough.assign(context=lambda inputs: format_docs(inputs["docs"]))
        | prompt
        | llm
        | StrOutputParser()
    )

    return RunnableParallel(
        docs=retriever,
        question=RunnablePassthrough()
    ).assign(answer=answer_chain)


def format_sources(docs):
    sources = []
    for doc in docs:
        sources.append({
            "filename": doc.metadata.get("filename"),
            "page_number": doc.metadata.get("page_number"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "preview": doc.page_content[:250]
        })
    return sources


def ask_question(question, document=None):
    chain = build_rag_chain(get_retriever(document), get_llm())
    result = chain.invoke(question)

    return {
        "answer": result["answer"],
        "sources": format_sources(result["docs"])
    }
