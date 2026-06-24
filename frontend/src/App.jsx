import { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://localhost:5001";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

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
    } catch (error) {
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
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAnswer(data.error || "Something went wrong.");
        return;
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error) {
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
        </section>

        <section className="card">
          <h2>2. Ask a Question</h2>
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