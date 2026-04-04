"""
Dogesh Assistant – Web Search Tool
Opens the default browser with a Google search.
"""

import webbrowser
import urllib.parse


def search_web(query: str) -> str:
    """Open Google search in the default browser. Returns a confirmation string."""
    if not query or not query.strip():
        return "Please provide a search query."
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f'Searching Google for "{query}"…'


def open_url(url: str) -> str:
    """Open an arbitrary URL in the default browser."""
    webbrowser.open(url)
    return f"Opening {url}…"
