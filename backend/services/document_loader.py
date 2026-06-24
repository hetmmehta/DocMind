from pypdf import PdfReader


def load_pdf_text(file_path):
    """
    Extract text from a PDF file.
    Returns a list of page dictionaries so we can preserve page numbers for citations later.
    """
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text:
            pages.append({
                "page_number": page_number,
                "text": text
            })

    return pages