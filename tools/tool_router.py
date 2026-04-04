"""
Dogesh Assistant – Tool Router
Maps LLM intent → Python function and returns a human-readable result.
"""

from tools.search import search_web, open_url


# ── Registry ──────────────────────────────────────────────────────────────────
_TOOLS = {
    "search_web": lambda params: search_web(params.get("query", "")),
    "open_url":   lambda params: open_url(params.get("url", "")),
    # Add more tools here:
    # "set_timer": lambda params: ...
    # "send_email": lambda params: ...
}


def execute(intent: str, parameters: dict) -> str:
    """
    Route an intent to the matching tool function.
    Returns a short result string (spoken / shown to user).
    """
    handler = _TOOLS.get(intent)
    if handler:
        try:
            return handler(parameters)
        except Exception as e:
            return f"Tool error ({intent}): {e}"
    # No matching tool → nothing extra to do for general_chat
    return ""


def list_tools() -> list:
    return list(_TOOLS.keys())
