# Kiwix RAG Server

Search offline ZIM archives (Wikipedia, DevDocs, etc.) and serve results as an OpenAPI tool for OpenWebUI.

Wrapper for https://github.com/mozanunal/llm-tools-kiwix for OpenWebUI.

## Quick Start

```bash
cd kiwix-rag-server
ZIM_HOST_DIR=/path/to/your/zim/files docker compose up --build -d
```

In **OpenWebUI** → Admin Panel → Tools, add: `http://<host-ip>:8100`

That's it. The LLM will search your ZIM files automatically.

## Config

Set via env vars or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ZIM_HOST_DIR` | `./zims` | Host directory containing `.zim` files |
| `RAG_PORT` | `8100` | Port to expose on the host |
| `MAX_ARTICLES` | `3` | Max articles returned per search |
| `MAX_CHARS` | `4000` | Max chars per article (truncation) |

Example `.env`:
```
ZIM_HOST_DIR=/data/wiki
RAG_PORT=8100
MAX_ARTICLES=5
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Health check |
| `GET /zims` | List available ZIMs |
| `POST /search` | Search (pass `{"query": "..."}`) |
| `GET /openapi.json` | OpenAPI spec |

## Local Dev

```bash
pip install -r requirements.txt
ZIM_DIR=/path/to/zims uvicorn main:app --host 0.0.0.0 --port 8100
```
