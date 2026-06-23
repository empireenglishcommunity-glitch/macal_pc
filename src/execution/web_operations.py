"""
Web Operations - Internet access for the agent.
Search the web, fetch pages, extract text from URLs.
Uses DuckDuckGo (free, no API key) and urllib (stdlib).
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import re
from typing import Optional


def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web using DuckDuckGo Instant Answer API.

    Args:
        query: Search query string
        max_results: Maximum results to return

    Returns:
        dict with success status and results list
    """
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        req = urllib.request.Request(url, headers={"User-Agent": "MACAL-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = []

        # Abstract (main answer)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Answer"),
                "snippet": data["Abstract"][:300],
                "url": data.get("AbstractURL", ""),
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:100],
                    "snippet": topic.get("Text", "")[:300],
                    "url": topic.get("FirstURL", ""),
                })

        # If no results from instant answer, try HTML scraping approach
        if not results:
            results = _search_html_fallback(query, max_results)

        if results:
            return {"success": True, "query": query, "results": results[:max_results]}
        else:
            return {"success": True, "query": query, "results": [], "note": "No results found"}

    except Exception as e:
        return {"success": False, "error": str(e), "query": query}


def _search_html_fallback(query: str, max_results: int = 5) -> list:
    """Fallback: scrape DuckDuckGo HTML results."""
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "MACAL-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")

        results = []
        # Extract result snippets from DDG HTML
        snippets = re.findall(r'class="result__snippet">(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        urls = re.findall(r'class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)

        for i in range(min(len(snippets), max_results)):
            results.append({
                "title": re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else "",
                "snippet": re.sub(r'<[^>]+>', '', snippets[i]).strip()[:300],
                "url": urls[i].strip() if i < len(urls) else "",
            })
        return results
    except Exception:
        return []


def fetch_url(url: str, max_chars: int = 5000) -> dict:
    """Fetch a web page and extract its text content.

    Args:
        url: URL to fetch
        max_chars: Maximum characters to return

    Returns:
        dict with success status and extracted text
    """
    try:
        if not url.startswith("http"):
            url = "https://" + url

        req = urllib.request.Request(url, headers={
            "User-Agent": "MACAL-Agent/1.0 (Desktop Assistant)",
            "Accept": "text/html,application/xhtml+xml,text/plain",
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()

            # Determine encoding
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            else:
                encoding = "utf-8"

            html = raw.decode(encoding, errors="replace")

        # Extract text from HTML
        text = _html_to_text(html)

        if len(text) > max_chars:
            text = text[:max_chars] + "\n... (truncated)"

        return {"success": True, "url": url, "content": text, "chars": len(text)}

    except urllib.error.HTTPError as e:
        return {"success": False, "url": url, "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}


def _html_to_text(html: str) -> str:
    """Simple HTML to text conversion (no external dependencies)."""
    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Add line breaks for readability
    text = re.sub(r'\s{3,}', '\n', text)
    return text
