# EasySheet (Lecture-to-LaTeX Aid Sheet)

Generate a clean, editable LaTeX aid sheet from messy lecture PDFs in minutes. Upload lectures, set constraints, and get a dense cheat sheet that preserves formulas and structure.

## Local setup

### 1) Backend (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Create a `.env` at the repo root (or `backend/.env`) with:

```bash
GEMINI_API_KEY=YOUR_KEY
PINECONE_API_KEY=YOUR_KEY
PINECONE_INDEX=lecture-aidsheet
PINECONE_DIMENSION=3072
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_DISABLED=false
GEMINI_FALLBACK=true
UPLOADS_DIR=./data/uploads
```

Start the API:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2) Web app (Next.js)

```bash
cd web
npm install
```

Create `web/.env.local`:

```bash
BACKEND_URL=http://localhost:8000
```

Start the web app:

```bash
npm run dev
```

Open http://localhost:3000

### 3) LaTeX preview (optional)

To compile and preview PDFs inside the app, install a LaTeX engine that provides `pdflatex` (e.g., MacTeX).
