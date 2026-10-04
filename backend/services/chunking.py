from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages, filename):
    """
    Convert extracted PDF pages into smaller chunks.
    Each chunk keeps metadata like filename and page number for citations.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    chunks = []

    for page in pages:
        page_number = page["page_number"]
        text = page["text"]

        split_texts = text_splitter.split_text(text)

        for index, chunk_text in enumerate(split_texts):
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_index": index
                }
            })

    return chunks