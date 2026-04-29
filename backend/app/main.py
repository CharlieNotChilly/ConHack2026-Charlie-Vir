from fastapi import FastAPI

from .routes import generate, ingest

app = FastAPI(title="Lecture-to-LaTeX Aid Sheet")

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
