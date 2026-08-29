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
        return KiwixSearchResponse(
            query=req.query,
            zim_file="(none)",
            match_count=0,
            articles=[{
                "path": "_hint_",
                "content": (
                    f"Multiple ZIMs available. Specify 'zim_file'. Options: "
                    f"{', '.join(os.path.basename(z) for z in available)}"
                ),
            }],
        )
    elif not target:
        return KiwixSearchResponse(
            query=req.query, zim_file="(none)", match_count=0, articles=[]
        )

    result = search_and_collect(target, req.query)
    return KiwixSearchResponse(**result)


# Explicitly handle OPTIONS for CORS preflight on all routes (including /openapi.json)
@app.api_route("/", methods=["OPTIONS"])
@app.api_route("/zims", methods=["OPTIONS"])
@app.api_route("/search", methods=["OPTIONS"])
@app.api_route("/openapi.json", methods=["OPTIONS"])
def cors_preflight():
    return {}
