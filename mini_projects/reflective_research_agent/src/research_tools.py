import os
import wikipedia
from typing import List, Dict
from dotenv import load_dotenv
from tavily import TavilyClient
import time, requests, xml.etree.ElementTree as ET

# utils
from .utils import clean_text, ensure_pdf_url, fetch_pdf_bytes, pdf_bytes_to_text, build_session

load_dotenv()
session = build_session()


# ----- arXiv search -----
def arxiv_search_tool(
    query: str,
    max_results: int = 3,
) -> List[Dict]:
    """
    Search arXiv and return results with `summary`
    """
    # ===== FLAGS INTERNS =====
    _INCLUDE_PDF = True
    _EXTRACT_TEXT = True
    _MAX_PAGES = 6
    _TEXT_CHARS = 5000
    _SAVE_FULL_TEXT = False
    _SLEEP_SECONDS = 1.0
    # ==========================

    api_url = (
        "https://export.arxiv.org/api/query"
        f"?search_query=all:{requests.utils.quote(query)}&start=0&max_results={max_results}"
    )

    out: List[Dict] = []
    try:
        resp = session.get(api_url, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return [{"error": f"arXiv API request failed: {e}"}]

    try:
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title = (
                    entry.findtext("atom:title", default="", namespaces=ns) or ""
            ).strip()
            published = (
                    entry.findtext("atom:published", default="", namespaces=ns) or ""
            )[:10]
            url_abs = entry.findtext("atom:id", default="", namespaces=ns) or ""
            # original abstract
            abstract_summary = (
                    entry.findtext("atom:summary", default="", namespaces=ns) or ""
            ).strip()

            authors = []
            for a in entry.findall("atom:author", ns):
                nm = a.findtext("atom:name", default="", namespaces=ns)
                if nm:
                    authors.append(nm)

            link_pdf = None
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    link_pdf = link.attrib.get("href")
                    break
            if not link_pdf and url_abs:
                link_pdf = ensure_pdf_url(url_abs)

            item = {
                "title": title,
                "authors": authors,
                "published": published,
                "url": url_abs,
                "summary": abstract_summary,
                "link_pdf": link_pdf,
            }

            pdf_bytes = None
            if (_INCLUDE_PDF or _EXTRACT_TEXT) and link_pdf:
                try:
                    pdf_bytes = fetch_pdf_bytes(session, link_pdf, timeout=90)
                    time.sleep(_SLEEP_SECONDS)
                except Exception as e:
                    item["pdf_error"] = f"PDF fetch failed: {e}"

            if _EXTRACT_TEXT and pdf_bytes:
                try:
                    text = pdf_bytes_to_text(pdf_bytes, max_pages=_MAX_PAGES)
                    text = clean_text(text) if text else ""
                    if text:
                        if _SAVE_FULL_TEXT:
                            item["pdf_text"] = text
                        else:
                            snippet = text[:_TEXT_CHARS].strip()
                            letters = sum(ch.isalpha() for ch in snippet)
                            spaces = snippet.count(" ")
                            longest_token = max(
                                (len(tok) for tok in snippet.split()), default=0
                            )
                            # Some PDFs extract as unreadable concatenated tokens; keep excerpt useful.
                            looks_unreadable = (
                                letters > 120
                                and (spaces / max(1, letters)) < 0.03
                                and longest_token > 80
                            )
                            if looks_unreadable:
                                item["pdf_text_excerpt"] = abstract_summary
                                item["pdf_text_warning"] = (
                                    "Extracted PDF text looked unreadable; using abstract."
                                )
                            else:
                                item["pdf_text_excerpt"] = snippet
                except Exception as e:
                    item["text_error"] = f"Text extraction failed: {e}"

            out.append(item)
        return out
    except ET.ParseError as e:
        return [{"error": f"arXiv API XML parse failed: {e}"}]
    except Exception as e:
        return [{"error": f"Unexpected error: {e}"}]



# ----- Tavily search -----
def tavily_search_tool(
    query: str, max_results: int = 5, include_images: bool = False
) -> list[dict]:
    """
    Perform a search using the Tavily API.

    Args:
        query (str): The search query.
        max_results (int): Number of results to return (default 5).
        include_images (bool): Whether to include image results.

    Returns:
        List[dict]: A list of dictionaries with keys like 'title', 'content', and 'url'.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")

    client = TavilyClient(api_key, base_url=os.getenv("DLAI_TAVILY_BASE_URL"))

    try:
        response = client.search(
            query=query, max_results=max_results, include_images=include_images
        )

        results = []
        for r in response.get("results", []):
            results.append(
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                }
            )

        if include_images:
            for img_url in response.get("images", []):
                results.append({"image_url": img_url})

        return results

    except Exception as e:
        return [{"error": str(e)}]  # For LLM-friendly agents



# ------ Wikipedia search tool --------
def wikipedia_search_tool(query: str, sentences: int = 5) -> List[Dict]:
    """
    Searches Wikipedia for a summary of the given query.

    Args:
        query (str): Search query for Wikipedia.
        sentences (int): Number of sentences to include in the summary.

    Returns:
        List[Dict]: A list with a single dictionary containing title, summary, and URL.
    """
    try:
        page_title = wikipedia.search(query)[0]
        page = wikipedia.page(page_title)
        summary = wikipedia.summary(page_title, sentences=sentences)

        return [{"title": page.title, "summary": summary, "url": page.url}]
    except Exception as e:
        return [{"error": str(e)}]



# if __name__ == "__main__":
    # for i in tavily_search_tool("multi-agent systems"):
    #     print(i)

    # for i in wikipedia_search_tool("multi-agent systems"):
    #     print(i)

    # for i in arxiv_search_tool("multi-agent systems"):
    #     print(i)



















