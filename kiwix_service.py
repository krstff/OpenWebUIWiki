"""Kiwix ZIM archive search service."""

import logging
import os
from glob import glob
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from libzim.reader import Archive
from libzim.search import Query, Searcher
from strip_tags import strip_tags

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ZIM_DIR = os.environ.get("ZIM_DIR", "./zims")
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "3"))
MAX_CHARS = int(os.environ.get("MAX_CHARS", "4000"))


def find_zim_files() -> List[str]:
    """Discover .zim files from ZIM_DIR."""
    return sorted(glob(f"{ZIM_DIR}/*.zim"))


def kiwix_search(zim_file_path: str, search_string: str) -> Tuple[int, List[str]]:
    """Search a ZIM file. Returns (match_count, list_of_article_paths)."""
    try:
        zim = Archive(Path(zim_file_path))
        query = Query().set_query(search_string)
        searcher = Searcher(zim)
        results = searcher.search(query)
        count = results.getEstimatedMatches()

        if count == 0:
            return 0, []

        limit = min(count, MAX_ARTICLES)
        paths = list(results.getResults(0, limit))
        return count, paths

    except FileNotFoundError:
        logger.error("ZIM file not found: %s", zim_file_path)
        return 0, []
    except Exception as e:
        logger.error("Search failed for '%s' in %s: %s", search_string, zim_file_path, e)
        return 0, []


def kiwix_read(zim_file_path: str, article_path: str) -> str:
    """Read a single article from a ZIM file and return plain text."""
    try:
        zim = Archive(Path(zim_file_path))
        entry = zim.get_entry_by_path(article_path)
        html = bytes(entry.get_item().content).decode("UTF-8")
        text = strip_tags(html, minify=True, remove_blank_lines=True)

        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n\n... [truncated]"
        return text.strip()

    except Exception as e:
        logger.error("Read failed for '%s' in %s: %s", article_path, zim_file_path, e)
        return f"[Error reading article '{article_path}']: {e}"


def search_and_collect(zim_file_path: str, search_string: str) -> dict:
    """Search a ZIM file and return content of matching articles."""
    count, paths = kiwix_search(zim_file_path, search_string)

    if not paths:
        return {
            "query": search_string,
            "zim_file": zim_file_path,
            "match_count": 0,
            "articles": [],
        }

    articles = []
    for path in paths:
        content = kiwix_read(zim_file_path, path)
        articles.append({"path": path, "content": content})

    return {
        "query": search_string,
        "zim_file": zim_file_path,
        "match_count": count,
        "articles": articles,
    }


def list_available_zims() -> List[dict]:
    """Return metadata about all discovered ZIM files."""
    zims = find_zim_files()
    result = []
    for z in zims:
        try:
            archive = Archive(Path(z))
            meta = {}
            for key in ("Name", "Creator", "Language"):
                val = archive.get_metadata(key)
                if val:
                    meta[key.lower()] = val.decode("utf-8", errors="replace") if isinstance(val, bytes) else val
            info = {
                "path": z,
                "title": meta.pop("name", Path(z).stem),
                **meta,
                "article_count": archive.article_count,
            }
        except Exception as e:
            info = {"path": z, "title": Path(z).stem, "error": str(e)}
        result.append(info)
    return result
