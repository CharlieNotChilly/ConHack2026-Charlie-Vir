import logging
import time

from fastapi import FastAPI, Request

from .routes import generate, ingest

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Lecture-to-LaTeX Aid Sheet")
logger = logging.getLogger("app.requests")

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
            },
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
