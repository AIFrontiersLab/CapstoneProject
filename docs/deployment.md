# Deployment

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example .env    # edit .env and set OPENAI_API_KEY if needed
mkdir -p data/uploads data/chroma
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000 (proxies `/api` to backend).

---

## Docker (local)

From project root:

```bash
cp .env.example .env
# Optionally set OPENAI_API_KEY in .env
docker compose up --build
```

- Backend: http://localhost:8000  
- Frontend: http://localhost:3000 (nginx serves the SPA and proxies `/api` to backend)

Data is persisted in the `rag_data` volume.

---

## Cloud deployment notes

- **Backend**: Run the backend container on any host (e.g. Render, Railway, ECS). Set env vars (`OPENAI_API_KEY`, `UPLOAD_DIR`, `CHROMA_PERSIST_DIR`, `SQLITE_PATH`). Use a persistent volume or external DB/vector store for production.
- **Frontend**: Build with `npm run build` and serve the `dist/` folder (e.g. Vercel, S3+CloudFront). Set `VITE_API_BASE` or equivalent to the backend URL if not using same-origin proxy.
- **Vector DB**: For scale, replace ChromaDB with Pinecone/Weaviate/Qdrant via the existing abstraction in `VectorStoreService` and `EmbeddingService`.
- **Auth**: Add API keys or OAuth in frontend and backend; protect `/documents/upload` and `/query` endpoints.
