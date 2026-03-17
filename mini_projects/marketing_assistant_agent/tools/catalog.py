import json
import os
from typing import Any

try:
    from db import get_products, get_product_by_id, get_sales_stats
except ModuleNotFoundError:
    from ..db import get_products, get_product_by_id, get_sales_stats


#Tavily web search

def tavily_search_tool(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for current trends and market intelligence."""
    from tavily import TavilyClient
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return [{"error": "TAVILY_API_KEY not set."}]
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)
        return [
            {"title": r.get("title", ""), "content": r.get("content", ""), "url": r.get("url", "")}
            for r in response.get("results", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]



#Product catalog

def product_catalog_tool(
    category: str | None = None,
    gender: str | None = None,
    age_group: str | None = None,
    season: str | None = None,
    max_items: int = 15,
) -> list[dict]:
    """Retrieve products from the internal catalog with optional filters."""
    products = get_products(
        gender=gender, age_group=age_group, season=season, min_stock=1
    )
    # Filter by category name if provided
    if category:
        products = [p for p in products if category.lower() in p.get("category_name", "").lower()]
    return products[:max_items]


def product_detail_tool(product_id: int) -> dict:
    """Get full details + sales stats for a specific product."""
    product = get_product_by_id(product_id)
    if not product:
        return {"error": f"Product {product_id} not found."}
    stats = get_sales_stats(product_id)
    return {**product, "sales_stats": stats}



# Tool def for LLM

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search_tool",
            "description": (
                "Search the web for current fashion/retail trends, competitor analysis, "
                "consumer sentiment, and market intelligence relevant to a product or category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {"type": "integer", "default": 5, "description": "Max results to return"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "product_catalog_tool",
            "description": (
                "Retrieve products from the internal retail catalog. "
                "Can filter by category, gender, age group, and season."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category":  {"type": "string", "description": "Product category (e.g. Sunglasses, Watches)"},
                    "gender":    {"type": "string", "enum": ["Men", "Women", "Unisex"], "description": "Target gender"},
                    "age_group": {"type": "string", "enum": ["Kids", "Teens", "Adults", "Seniors"], "description": "Target age group"},
                    "season":    {"type": "string", "enum": ["Spring", "Summer", "Autumn", "Winter"], "description": "Target season"},
                    "max_items": {"type": "integer", "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "product_detail_tool",
            "description": "Get detailed information and sales statistics for a specific product by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "The product's database ID"},
                },
                "required": ["product_id"],
            },
        },
    },
]

#tool mapping
_TOOLS_MAP = {
    "tavily_search_tool": tavily_search_tool,
    "product_catalog_tool": product_catalog_tool,
    "product_detail_tool": product_detail_tool,
}


def handle_tool_call(tool_call) -> Any:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")
    fn = _TOOLS_MAP.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    return fn(**args)


def create_tool_response_message(tool_call, result) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.function.name,
        "content": json.dumps(result, default=str),
    }