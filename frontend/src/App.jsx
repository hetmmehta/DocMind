import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState("");

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      const data = await response.json();

      if (response.ok) {
        setDocuments(data.documents || []);
      }
    } catch {
      // The backend may not be running yet; the upload/ask flows show their own errors.
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (filename) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/documents/${encodeURIComponent(filename)}`,
        { method: "DELETE" }
      );
      const data = await response.json();

      if (!response.ok) {
        setUploadStatus(data.error || "Delete failed.");
        return;
      }

      if (selectedDocument === filename) {
        setSelectedDocument("");
      }
      setUploadStatus(`${filename} removed.`);
      loadDocuments();
    } catch {
      setUploadStatus("Could not connect to backend.");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus("Please choose a PDF first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setUploadStatus("");

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setUploadStatus(data.error || "Upload failed.");
        return;
      }

      setUploadStatus(
        `${data.filename} uploaded successfully. ${data.chunks_stored} chunks stored.`
      );
      loadDocuments();
    } catch {
      setUploadStatus("Could not connect to backend.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) {
      setAnswer("Please enter a question.");
      return;
    }

    setIsAsking(true);
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          document: selectedDocument || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAnswer(data.error || "Something went wrong.");
        return;
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch {
      setAnswer("Could not connect to backend.");
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <header>
          <p className="eyebrow">RAG-Powered Personal Knowledge Base</p>
          <h1>DocMind</h1>
          <p className="subtitle">
            Upload a PDF and ask questions grounded in your own documents.
          </p>
        </header>

        <section className="card">
          <h2>1. Upload PDF</h2>
          <div className="upload-row">
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <button onClick={handleUpload} disabled={isUploading}>
              {isUploading ? "Uploading..." : "Upload"}
            </button>
          </div>
          {uploadStatus && <p className="status">{uploadStatus}</p>}

          {documents.length > 0 && (
            <ul className="document-list">
              {documents.map((doc) => (
                <li key={doc.filename}>
                  <span>
                    <strong>{doc.filename}</strong> · {doc.pages} pages ·{" "}
                    {doc.chunks} chunks
                  </span>
                  <button
                    className="link-button"
                    onClick={() => handleDelete(doc.filename)}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2>2. Ask a Question</h2>
          {documents.length > 1 && (
            <select
              className="document-select"
              value={selectedDocument}
              onChange={(e) => setSelectedDocument(e.target.value)}
            >
              <option value="">Search all documents</option>
              {documents.map((doc) => (
                <option key={doc.filename} value={doc.filename}>
                  Only {doc.filename}
                </option>
              ))}
            </select>
          )}
          <textarea
            placeholder="Example: What projects has Het worked on?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button onClick={handleAsk} disabled={isAsking}>
            {isAsking ? "Thinking..." : "Ask DocMind"}
          </button>

          {answer && (
            <div className="answer-box">
              <h3>Answer</h3>
              <p>{answer}</p>
            </div>
          )}

          {sources.length > 0 && (
            <div className="sources">
              <h3>Sources</h3>
              {sources.map((source, index) => (
                <div className="source-card" key={index}>
                  <strong>
                    {source.filename}, page {source.page_number}
                  </strong>
                  <p>{source.preview}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;