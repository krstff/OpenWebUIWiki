"""FastAPI server exposing Kiwix ZIM search as OpenAPI tools for OpenWebUI."""

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from kiwix_service import (
    find_zim_files,
    list_available_zims,
    search_and_collect,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Kiwix RAG Tool",
    description=(
        "Search offline Kiwix ZIM archives (Wikipedia, Stack Exchange, DevDocs) "
        "and return article content for use as a RAG knowledge base in OpenWebUI."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class KiwixSearchRequest(BaseModel):
    query: str = "Your question or search terms"
    zim_file: Optional[str] = None


class KiwixSearchResponse(BaseModel):
    query: str
    zim_file: str
    match_count: int
    articles: list


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "zim_files_found": len(find_zim_files())}


@app.get("/zims", tags=["catalog"])
def get_zims():
    """List all available ZIM archives with metadata."""
    return {"zims": list_available_zims()}


@app.post("/search", response_model=KiwixSearchResponse, tags=["rag"])
def search_kiwix(req: KiwixSearchRequest):
    """Full-text search a ZIM archive and return article content."""
    available = find_zim_files()

    target = req.zim_file
    if not target and len(available) == 1:
        target = available[0]
    elif not target and available:
        # Auto-select: prefer English ZIM, fall back to first available
        en_zims = [z for z in available if "wikipedia_en" in os.path.basename(z).lower()]
        target = en_zims[0] if en_zims else available[0]  # default to English or first
    elif not target:
        return KiwixSearchResponse(
            query=req.query, zim_file="(none)", match_count=0, articles=[]
        )

    result = search_and_collect(target, req.query)

    # If no matches, give the LLM actionable feedback
    if result["match_count"] == 0 and not result["articles"]:
        try:
            from libzim.reader import Archive
            from pathlib import Path
            archive = Archive(Path(target))
            lang_code = archive.get_metadata("Language")
            lang_str = (
                lang_code.decode("utf-8", errors="replace")
                if isinstance(lang_code, bytes)
                else str(lang_code)
            )
        except Exception:
            lang_str = "unknown"

        result["articles"] = [{
            "path": "_no_results_",
            "content": (
                f"No results found for query '{req.query}' in this ZIM archive "
                f"(language: {lang_str}). The archive may be in a different language. "
                f"Try rephrasing the query in that language, or check /zims for "
                f"available archives matching your query language."
            ),
        }]

    return KiwixSearchResponse(**result)


# Explicitly handle OPTIONS for CORS preflight on all routes (including /openapi.json)
@app.api_route("/", methods=["OPTIONS"])
@app.api_route("/zims", methods=["OPTIONS"])
@app.api_route("/search", methods=["OPTIONS"])
@app.api_route("/openapi.json", methods=["OPTIONS"])
def cors_preflight():
    return {}
