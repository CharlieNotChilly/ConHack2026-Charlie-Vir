# Plan: Lecture-to-LaTeX Aid Sheet Web App

Date: 2026-04-28
Owner: Team ConHack2026
Status: Draft

## Goals
- Web app that ingests many lecture PDFs and generates a LaTeX-formatted aid sheet.
- Exact formula fidelity (no paraphrasing or lossy math rendering).
- Runtime constraint: end-to-end generation in 5 minutes per request.
- User can edit generated LaTeX before final PDF export.
- Use Gemini models where possible; use other providers (e.g., Voyage AI) for multimodal embeddings if needed.

## Non-Goals (for v1)
- Non-PDF inputs (PPTX, DOCX, images) beyond conversion-to-PDF.
- Full text search UI (basic query UI only).
- Collaborative real-time editing.

## User Flow
1. User uploads lecture PDFs.
2. System parses each page: separate text, formulas, and images.
3. System builds a knowledge base (Pinecone vectors + metadata).
4. User sets target page count + special instructions (e.g., include image X from page Y).
5. System retrieves and assembles content with exact formulas.
6. System generates editable LaTeX draft.
7. User edits LaTeX in-browser and exports PDF.

## Architecture Overview
- Frontend: React (Next.js App Router) + Monaco editor for LaTeX editing.
- Backend API: Node.js (Next.js API routes) or Python service for parsing pipeline.
- Storage:
  - Object storage for PDFs and extracted images.
  - Vector DB: Pinecone for text/image embeddings.
  - Relational DB: Postgres for metadata (lectures, pages, assets, jobs).
- LLM/Embeddings:
  - Gemini for text and reasoning.
  - Voyage AI (or other) for image embeddings if Gemini multimodal is not sufficient.
- Rendering:
  - LaTeX engine (latexmk) in a sandboxed worker.

## Data Model (Draft)
- Lecture(id, course_id, filename, uploaded_at)
- Page(id, lecture_id, page_number, text, ocr_text, width, height)
- Asset(id, page_id, type=image, hash, storage_url, bbox)
- Chunk(id, page_id, chunk_text, bbox, embedding_id)
- VectorRef(id, type=text|image, pinecone_id, metadata_json)
- AidSheet(id, user_id, request_json, latex_source, pdf_url, created_at)

## Parsing and Formula Fidelity
- Extract text and layout from PDF pages using a layout-aware parser.
- For formulas:
  - Prefer native PDF math extraction if available.
  - Fall back to formula OCR (Mathpix or similar) for exact LaTeX.
  - Preserve inline vs display math and page coordinates.
- Store formula text separately to enforce fidelity in generation.

## Knowledge Base Construction
- Chunk by page and semantic structure (title, bullets, formula blocks).
- Embeddings:
  - Text: Gemini text embedding model.
  - Images: Voyage AI image embedding model if needed.
- Pinecone metadata includes lecture/page, bbox, and type for filtering.

## Retrieval and Assembly
- RAG pipeline builds a shortlist of:
  - text chunks
  - formulas (exact LaTeX)
  - images
- Constraints parser enforces user instructions (forced includes).
- Content assembler selects items to fit requested page count.
- Heuristic for page budgeting:
  - estimate line counts for text
  - reserve blocks for formulas and images

## LaTeX Generation
- Standard template with tight margins and multi-column layout.
- Insert exact formulas without paraphrase.
- Include figures with captions and references.
- Output draft LaTeX and compile to PDF for preview.
- Provide in-browser LaTeX editor with live PDF refresh.

## Performance Targets
- Parsing + extraction: <= 2 min for typical class set (<= 200 pages).
- Embedding + indexing: <= 1.5 min with batch jobs.
- Retrieval + assembly + LaTeX generation: <= 1.5 min.
- Total <= 5 min per request with caching and pre-processing.

## Security and Privacy
- Store PDFs and images in private buckets.
- Short-lived signed URLs for access.
- Tenant isolation via course/user scoping in metadata.

## Risks and Mitigations
- Formula fidelity is hard from rasterized math.
  - Mitigation: allow selective manual fixes in editor; prioritize Mathpix.
- 5-minute constraint under large inputs.
  - Mitigation: pre-process and cache embeddings on upload; async queues.
- PDF parsing variability.
  - Mitigation: fallback parsers and validation checks.

## MVP Milestones
1. PDF ingestion + extraction pipeline.
2. Pinecone indexing and basic retrieval.
3. Constraint-aware assembly of content.
4. LaTeX draft generation + preview.
5. In-browser LaTeX editing and export.

## Open Questions
- Exact choice of formula OCR provider (Mathpix vs open-source alternatives).
- Whether to run parsing in Python microservice vs Node worker.
- Maximum PDF size and concurrency targets.
