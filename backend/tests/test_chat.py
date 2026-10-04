import pytest
from google.api_core.exceptions import ResourceExhausted
from langchain_core.documents import Document
from langchain_core.language_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from services import rag_chain
from services.errors import QUOTA_ERROR_MESSAGE

DOCS = [
    Document(
        page_content="Het built DocMind, a RAG app for PDFs.",
        metadata={"filename": "Profile.pdf", "page_number": 2, "chunk_index": 0},
    ),
    Document(
        page_content="DocMind uses Gemini and ChromaDB.",
        metadata={"filename": "Report.pdf", "page_number": 5, "chunk_index": 3},
    ),
]


@pytest.fixture
def retriever_calls(monkeypatch):
    calls = []

    def fake_get_retriever(document=None):
        calls.append(document)
        return RunnableLambda(lambda question: DOCS)

    monkeypatch.setattr(rag_chain, "get_retriever", fake_get_retriever)
    return calls


def test_chat_returns_answer_and_sources(client, monkeypatch, retriever_calls):
    monkeypatch.setattr(
        rag_chain, "get_llm",
        lambda: FakeListChatModel(responses=["Het built DocMind (Profile.pdf, page 2)."]),
    )

    response = client.post("/chat", json={"question": "What did Het build?"})

    assert response.status_code == 200
    body = response.get_json()
    assert body["answer"] == "Het built DocMind (Profile.pdf, page 2)."
    assert body["sources"] == [
        {
            "filename": "Profile.pdf",
            "page_number": 2,
            "chunk_index": 0,
            "preview": "Het built DocMind, a RAG app for PDFs.",
        },
        {
            "filename": "Report.pdf",
            "page_number": 5,
            "chunk_index": 3,
            "preview": "DocMind uses Gemini and ChromaDB.",
        },
    ]
    assert retriever_calls == [None]


def test_prompt_contains_retrieved_context_and_rules(retriever_calls, monkeypatch):
    prompts = []

    def fake_llm(prompt_value):
        prompts.append(prompt_value)
        return "ok"

    monkeypatch.setattr(rag_chain, "get_llm", lambda: RunnableLambda(fake_llm))

    rag_chain.ask_question("What did Het build?")

    system, human = prompts[0].to_messages()
    assert rag_chain.NOT_FOUND_MESSAGE in system.content
    assert "Source: Profile.pdf, page 2\nHet built DocMind" in human.content
    assert "What did Het build?" in human.content


def test_chat_can_scope_to_one_document(client, monkeypatch, retriever_calls):
    monkeypatch.setattr(rag_chain, "get_llm", lambda: FakeListChatModel(responses=["ok"]))

    response = client.post("/chat", json={"question": "Summary?", "document": "Report.pdf"})

    assert response.status_code == 200
    assert retriever_calls == ["Report.pdf"]


def test_chat_quota_error_returns_clean_429(client, monkeypatch, retriever_calls):
    def quota_exceeded(prompt_value):
        raise ResourceExhausted("429 You exceeded your current quota")

    monkeypatch.setattr(rag_chain, "get_llm", lambda: RunnableLambda(quota_exceeded))

    response = client.post("/chat", json={"question": "Anything?"})

    assert response.status_code == 429
    assert response.get_json() == {"error": QUOTA_ERROR_MESSAGE}


def test_chat_unexpected_error_is_not_leaked(client, monkeypatch, retriever_calls):
    def boom(prompt_value):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(rag_chain, "get_llm", lambda: RunnableLambda(boom))

    response = client.post("/chat", json={"question": "Anything?"})

    assert response.status_code == 500
    assert "secret internal detail" not in response.get_data(as_text=True)


@pytest.mark.parametrize("payload", [None, {}, {"question": ""}, {"question": "   "}, {"question": 42}])
def test_chat_requires_a_question(client, payload):
    response = client.post("/chat", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Question is required"}
