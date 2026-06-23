# tools.py
# Gives agents the ability to search the web using DuckDuckGo (via the ddgs package)

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> list:
    """
    Searches the web using DuckDuckGo and returns a list of results.
    Each result has a title, snippet (body text), and URL.
    """
    results = []

    with DDGS() as ddgs:
        search_results = ddgs.text(query, max_results=max_results)

        for result in search_results:
            results.append({
                "title": result.get("title", ""),
                "snippet": result.get("body", ""),
                "url": result.get("href", "")
            })

    return results


def format_search_results(results: list) -> str:
    """
    Converts search results into a clean text block
    that we can feed into an LLM prompt.
    """
    if not results:
        return "No search results found."

    formatted = []
    for i, r in enumerate(results, start=1):
        formatted.append(
            f"[Source {i}] {r['title']}\n{r['snippet']}\nURL: {r['url']}\n"
        )

    return "\n".join(formatted)