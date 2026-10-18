"""
Web search module for JARVIS using DuckDuckGo.
Provides reliable, free, real-time web research, sources, and summaries.
"""

from typing import List, Dict, Any, Optional
import httpx
from jarvis.core.logger import jarvis_logger

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False


class WebSearchTool:
    def __init__(self):
        self.has_ddgs = HAS_DDGS

    def search(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """
        Execute web search and return list of results:
        [{'title': ..., 'url': ..., 'snippet': ...}]
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        jarvis_logger.info(f"Performing web search for: '{clean_query}'")

        # Try DDGS library
        if self.has_ddgs:
            try:
                results = []
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(clean_query, max_results=max_results))
                    for item in raw_results:
                        results.append({
                            "title": item.get("title", "Untitled"),
                            "url": item.get("href") or item.get("link", ""),
                            "snippet": item.get("body") or item.get("snippet", "")
                        })
                if results:
                    return results
            except Exception as e:
                jarvis_logger.warning(f"DDGS search failed: {e}. Trying HTTP fallback.")

        # Resilient HTTP fallback using DuckDuckGo Instant Answer API
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": clean_query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            with httpx.Client(timeout=8.0) as client:
                res = client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    abstract = data.get("AbstractText")
                    abstract_url = data.get("AbstractURL")
                    if abstract:
                        results.append({
                            "title": data.get("Heading", "Instant Answer"),
                            "url": abstract_url or "https://duckduckgo.com",
                            "snippet": abstract
                        })
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if "Text" in topic and "FirstURL" in topic:
                            results.append({
                                "title": topic["Text"].split(" - ")[0] if " - " in topic["Text"] else topic["Text"][:60],
                                "url": topic["FirstURL"],
                                "snippet": topic["Text"]
                            })
                    if results:
                        return results
        except Exception as e:
            jarvis_logger.error(f"HTTP web search fallback failed: {e}")

        return []

    def format_search_context(self, results: List[Dict[str, str]]) -> str:
        """Format search results into a clean prompt context block with citations."""
        if not results:
            return "No web search results found."

        formatted = ["Web Search Research Results:"]
        for idx, item in enumerate(results, start=1):
            formatted.append(
                f"[{idx}] Title: {item['title']}\n"
                f"    Source URL: {item['url']}\n"
                f"    Snippet: {item['snippet']}\n"
            )
        return "\n".join(formatted)


web_search_tool = WebSearchTool()
