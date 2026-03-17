import os
from datetime import datetime
from typing import Generator

import openai

try:
    from tools import TOOL_DEFINITIONS, handle_tool_call, create_tool_response_message
except ModuleNotFoundError:
    from ..tools import TOOL_DEFINITIONS, handle_tool_call, create_tool_response_message

from dotenv import load_dotenv
load_dotenv()

def market_research_agent(
    product: dict,
    filters: dict,
    stream_callback=None,
) -> dict:
    """
    Runs the market research agent for a specific product and campaign filters.

    Args:
        product:         Full product dict from the DB.
        filters:         Dict with keys: gender, age_group, season, tone, campaign_goal.
        stream_callback: Optional callable(step: str, data: str) for streaming logs.

    Returns:
        dict with keys: trend_summary, recommended_product, justification, messages
    """

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _log(step: str, data: str):
        if stream_callback:
            stream_callback(step, data)

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
You are an expert retail marketing research analyst. Your task is to conduct market research
for a campaign around the following product:

**Product:** {product['name']} ({product.get('category_name', '')})
**Brand:** {product.get('brand', 'N/A')}
**Description:** {product.get('description', '')}
**Price:** ${product.get('price', 0):.2f}
**Tags:** {product.get('tags', '')}
**Target Audience:** {filters.get('gender','All')} | {filters.get('age_group','All')} | Season: {filters.get('season','All')}
**Campaign Goal:** {filters.get('campaign_goal', 'Brand awareness')}
**Brand Tone:** {filters.get('tone', 'Modern and aspirational')}
**Today's date:** {today}

Your research steps:
1. Search for 2-3 current fashion/retail trends relevant to this product and audience.
2. Search for consumer sentiment or lifestyle trends matching the target demographic.
3. Review the internal product catalog to understand where this product sits.
4. Synthesize findings into a clear trend summary.

Conclude with a structured analysis:
- **Top Trends** (2-3 bullet points)
- **Consumer Insights** (1-2 sentences)
- **Campaign Angle** (the core positioning idea)
- **Product Fit Score** (1-10) with justification
"""

    messages = [{"role": "user", "content": prompt}]
    _log("start", f"🔍 Starting market research for **{product['name']}**")

    max_iterations = 8
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                _log("tool_call", f"🛠 Calling `{tc.function.name}` → {tc.function.arguments[:120]}...")
                result = handle_tool_call(tc)
                _log("tool_result", f"📋 `{tc.function.name}` returned {len(str(result))} chars")
                messages.append(create_tool_response_message(tc, result))
        elif msg.content:
            _log("done", msg.content)
            return {
                "trend_summary": msg.content,
                "messages": messages,
            }
        else:
            break

    return {"trend_summary": "[Research incomplete]", "messages": messages}
