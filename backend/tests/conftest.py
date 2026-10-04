import os
import tempfile

# Configure the app before it is imported: no real API key, no telemetry,
# and storage in a throwaway directory so tests never touch real data.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="docmind-tests-")
os.environ["GOOGLE_API_KEY"] = "test-key-not-real"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["UPLOAD_FOLDER"] = os.path.join(_TEST_DATA_DIR, "uploads")
os.environ["CHROMA_DB_DIR"] = os.path.join(_TEST_DATA_DIR, "chroma_db")

import pytest  # noqa: E402

from app import create_app  # noqa: E402


def make_pdf(text="Hello DocMind"):
    """
    Build a tiny single-page PDF with real extractable text.
    """
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    pdf += f"startxref\n{xref_offset}\n%%EOF\n".encode()
    return pdf


@pytest.fixture
def upload_dir(tmp_path):
    path = tmp_path / "uploads"
    path.mkdir()
    return path


@pytest.fixture
def app(upload_dir):
    return create_app({
        "TESTING": True,
        "UPLOAD_FOLDER": str(upload_dir),
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    })


@pytest.fixture
def client(app):
    return app.test_client()
