# DocMind – RAG-Powered Personal Knowledge Base

DocMind is a full-stack RAG application that lets users upload PDFs and ask natural-language questions grounded in the uploaded document.

The app extracts text from PDFs, chunks the content, generates embeddings using Gemini, stores them in ChromaDB, and retrieves the most relevant chunks at query time. Gemini then generates an answer using only the retrieved context, with source attribution.

## Features

- PDF upload
- Text extraction from PDF files
- Recursive chunking with metadata
- Gemini embeddings
- ChromaDB vector storage
- Semantic retrieval
- Gemini-powered question answering
- Source attribution with filename and page number
- React frontend with upload and chat interface
- Flask REST API backend
- Error handling for API quota failures

## Tech Stack

**Frontend**
- React
- Vite
- CSS

**Backend**
- Python
- Flask
- LangChain
- ChromaDB
- Google Gemini API
- PyPDF

## Project Structure

```text
DocMind/
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── upload_routes.py
│   │   └── chat_routes.py
│   ├── services/
│   │   ├── document_loader.py
│   │   ├── chunking.py
│   │   ├── vector_store.py
│   │   └── rag_chain.py
│   ├── uploads/
│   ├── chroma_db/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
│
├── .gitignore
└── README.md

## Project Structure

User uploads a PDF.
The backend extracts text from the PDF page by page.
Text is split into overlapping chunks.
Each chunk is embedded using Gemini embeddings.
Chunks are stored in ChromaDB with metadata.
When the user asks a question, the app retrieves the top relevant chunks.
Gemini generates an answer using only the retrieved document context.
The app returns the answer along with source references.

## Backend Setup

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### Create a .env file inside backend/:

GOOGLE_API_KEY=your_google_api_key_here

### Run the backend:

python app.py

### Backend runs on:

http://localhost:5001

## Frontend Setup

cd frontend
npm install
npm run dev

### Frontend runs on:

http://localhost:5173