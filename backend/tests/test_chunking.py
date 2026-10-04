from services.chunking import chunk_pages


def _long_text(marker, sentences=60):
    return " ".join(f"{marker} sentence number {i} has some words in it." for i in range(sentences))


def test_chunks_keep_filename_and_page_metadata():
    pages = [
        {"page_number": 1, "text": _long_text("alpha")},
        {"page_number": 2, "text": _long_text("beta")},
    ]

    chunks = chunk_pages(pages, "notes.pdf")

    assert len(chunks) > 2
    for chunk in chunks:
        assert chunk["metadata"]["filename"] == "notes.pdf"
        assert chunk["metadata"]["page_number"] in (1, 2)
        assert len(chunk["text"]) <= 1000


def test_chunks_never_span_pages():
    pages = [
        {"page_number": 1, "text": _long_text("alpha")},
        {"page_number": 2, "text": _long_text("beta")},
        {"page_number": 3, "text": "A short final page."},
    ]
    page_text = {page["page_number"]: page["text"] for page in pages}

    chunks = chunk_pages(pages, "notes.pdf")

    for chunk in chunks:
        # Every chunk must come entirely from the page it is labelled with.
        assert chunk["text"] in page_text[chunk["metadata"]["page_number"]]

    assert {chunk["metadata"]["page_number"] for chunk in chunks} == {1, 2, 3}


def test_chunk_index_restarts_on_each_page():
    pages = [
        {"page_number": 1, "text": _long_text("alpha")},
        {"page_number": 2, "text": _long_text("beta")},
    ]

    chunks = chunk_pages(pages, "notes.pdf")

    for page_number in (1, 2):
        indexes = [c["metadata"]["chunk_index"] for c in chunks if c["metadata"]["page_number"] == page_number]
        assert indexes == list(range(len(indexes)))
