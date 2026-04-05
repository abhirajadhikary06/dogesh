"""
Dogesh Assistant – Web Search Tool
Fetches a short answer from Google search results and returns it for in-app display.
"""

from __future__ import annotations

import html
import re
import urllib.parse

import requests


def search_web(query: str) -> str:
    """Fetch a concise summary from Google search results."""
    if not query or not query.strip():
        return "Please provide a search query."
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.google.com/search?q={encoded}&hl=en&num=5&gbv=1"

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
                )
            },
            timeout=12,
        )
        response.raise_for_status()
    except Exception:
        return f'I could not fetch Google results for "{query}" right now.'

    page = response.text
    snippets = []

    for pattern in (
        r'<div[^>]+class="VwiC3b[^\"]*"[^>]*>(.*?)</div>',
        r'<span[^>]+class="aCOpRe"[^>]*>(.*?)</span>',
        r'<h3[^>]*>(.*?)</h3>',
    ):
        for match in re.finditer(pattern, page, re.IGNORECASE | re.DOTALL):
            raw = html.unescape(match.group(1))
            cleaned = re.sub(r"<[^>]+>", " ", raw)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned and cleaned not in snippets:
                snippets.append(cleaned)
            if len(snippets) >= 3:
                break
        if snippets:
            break

    if snippets:
        return " ".join(snippets[:2])

    title_match = re.search(r"<title>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip()
        return title.replace(" - Google Search", "")

    return f'I found Google results for "{query}", but could not extract a readable answer.'


def open_url(url: str) -> str:
    """Open an arbitrary URL in the default browser."""
    return f"Opening {url}…"
