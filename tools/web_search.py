import os
from .search_with_serp_api import _search_with_serpapi

def web_search(query: str) -> str:
    """A web search tool that uses SerpAPI with retry logic, or falls back to knowledge base."""
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    if serpapi_key:
        return _search_with_serpapi(query, serpapi_key)
    else:
        return "No SerpAPI key found"

