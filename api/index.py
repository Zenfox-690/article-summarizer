"""FastAPI entry point for the AI Article Summarizer (Vercel Serverless Function & local server)."""

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is available on sys.path for importing article_summarizer
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import article_summarizer

# Load .env in local environments
load_dotenv(ROOT_DIR / ".env")

MAX_ARTICLE_CHARACTERS = 100_000


class SummarizeRequest(BaseModel):
    article: str = Field(..., description="The article content to summarize")


class SummarizeResponse(BaseModel):
    summary: str


def map_gemini_exception_to_http(error: Exception) -> tuple[int, str]:
    """Map Gemini SDK and network exceptions to an appropriate HTTP status code and safe message."""
    error_code = getattr(error, "code", None)
    if not isinstance(error_code, int):
        error_code = getattr(error, "status_code", None)

    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Authentication or permissions error
    if error_code in (401, 403) or (
        error_code == 400
        and any(m in error_str for m in ("api_key_invalid", "api key not valid", "invalid api key"))
    ):
        return (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Gemini API authentication failed. Please verify the server GEMINI_API_KEY.",
        )

    # Malformed upstream request
    if error_code == 400:
        return status.HTTP_400_BAD_REQUEST, "Invalid request sent to Gemini API."

    # Rate limiting / Quota exhaustion
    if (
        error_code == 429
        or "resource_exhausted" in error_str
        or "quota" in error_str
        or "rate limit" in error_str
    ):
        return (
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Gemini rate limit or quota exceeded. Please try again later.",
        )

    # Timeout errors
    if (
        isinstance(error, TimeoutError)
        or error_code == 504
        or "timeout" in error_type
        or "timed out" in error_str
        or "deadline_exceeded" in error_str
    ):
        return (
            status.HTTP_504_GATEWAY_TIMEOUT,
            "Request to Gemini API timed out. Please try again later.",
        )

    # Retries exhausted
    if (
        any(r in error_str for r in ("retry", "retries"))
        and any(e in error_str for e in ("exhaust", "failed", "limit", "max"))
    ) or "retry_exhausted" in error_str:
        return (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Gemini request retries exhausted. Service is temporarily unavailable.",
        )

    # Transient 500 / 502 / 503 from provider
    if error_code in (500, 502, 503) or "unavailable" in error_str:
        return (
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Gemini service is temporarily unavailable. Please retry later.",
        )

    # Network connection issues
    if any(m in error_type for m in ("connect", "network", "transport")):
        return (
            status.HTTP_502_BAD_GATEWAY,
            "Network connection to Gemini API failed. Please check connectivity and retry.",
        )

    # Empty response
    if "empty summary" in error_str:
        return (
            status.HTTP_502_BAD_GATEWAY,
            "Gemini returned an empty summary.",
        )

    # General fallback - do not leak stack traces
    return (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Failed to summarize article with Gemini. Please try again later.",
    )


def load_file_content(filename: str) -> tuple[str, str]:
    """Load content of a frontend file from api/ or public/ directory."""
    candidates = [
        Path(__file__).parent / filename,
        ROOT_DIR / "public" / filename,
        Path.cwd() / "public" / filename,
        Path.cwd() / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8"), str(p)
    return "", ""


app = FastAPI(
    title="AI Article Summarizer API",
    description="Summarize article text using Google Gemini",
    version="1.0.0",
    redirect_slashes=False,
)


@app.middleware("http")
async def vercel_path_normalizer(request: Request, call_next):
    """Normalize request path if Vercel rewrote the URL to /api/index.py or /index.py."""
    path = request.scope.get("path", "")
    if path in ("/api/index.py", "/index.py", "/api/index", "/api/index/"):
        matched_path = request.headers.get("x-matched-path")
        if matched_path and matched_path not in ("/api/index.py", "/index.py", "/api/index"):
            request.scope["path"] = matched_path
        elif "path" in request.query_params:
            request.scope["path"] = request.query_params["path"]

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid request body. 'article' string field is required."},
    )


# Root and frontend endpoints (both FastAPI fallback and local serving)
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def serve_root():
    content, _ = load_file_content("index.html")
    if content:
        return HTMLResponse(content=content, status_code=status.HTTP_200_OK)
    return HTMLResponse(
        content="<!DOCTYPE html><html><body><h1>AI Article Summarizer</h1></body></html>",
        status_code=status.HTTP_200_OK,
    )


@app.get("/style.css")
def serve_css():
    content, _ = load_file_content("style.css")
    if content:
        return Response(content=content, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")


@app.get("/app.js")
def serve_js():
    content, _ = load_file_content("app.js")
    if content:
        return Response(content=content, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js not found")


# Health check endpoints
@app.get("/api/health")
@app.get("/health")
@app.get("/api")
@app.get("/api/index.py")
@app.get("/index.py")
def health():
    return {"status": "ok"}


# Summarization endpoints
@app.post("/api/summarize", response_model=SummarizeResponse)
@app.post("/summarize", response_model=SummarizeResponse)
@app.post("/api/index.py", response_model=SummarizeResponse)
@app.post("/index.py", response_model=SummarizeResponse)
def summarize(payload: SummarizeRequest):
    article = payload.article
    if not article or not article.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article text cannot be empty.",
        )

    if len(article) > MAX_ARTICLE_CHARACTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article exceeds maximum allowed length of {MAX_ARTICLE_CHARACTERS:,} characters.",
        )

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured on the server.",
        )

    try:
        summary_text = article_summarizer.summarize_article(
            article=article,
            api_key=api_key,
        )
    except Exception as exc:
        status_code, message = map_gemini_exception_to_http(exc)
        raise HTTPException(status_code=status_code, detail=message) from None

    return SummarizeResponse(summary=summary_text)
