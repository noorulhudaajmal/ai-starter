import base64
import json
import re

import openai

from dotenv import load_dotenv
load_dotenv()

def copywriter_agent(
    product: dict,
    image_path: str,
    trend_summary: str,
    caption: str,
    tagline: str,
    filters: dict,
    stream_callback=None,
) -> dict:
    """
    Analyzes the generated image + trends and produces campaign copy.

    Returns:
        dict: quote, justification, hashtags, ad_copy_variants, cta
    """

    import os
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _log(step, data):
        if stream_callback:
            stream_callback(step, data)

    _log("start", "✍️ Copywriter Agent crafting campaign copy...")

    # Encode image as base64
    with open(image_path, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode("utf-8")

    tone = filters.get("tone", "aspirational")
    audience = f"{filters.get('gender','All')} | {filters.get('age_group','Adults')} | {filters.get('season','All')} season"

    messages = [
        {
            "role": "system",
            "content": (
                "You are an award-winning copywriter specialising in fashion and lifestyle brands. "
                "You create concise, evocative, high-converting campaign copy."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_img}", "detail": "low"},
                },
                {
                    "type": "text",
                    "text": f"""
Product: {product['name']} — {product.get('description','')}
Trend summary: {trend_summary[:600]}
Existing caption: "{caption}"
Existing tagline: "{tagline}"
Target audience: {audience}
Brand tone: {tone}
Campaign goal: {filters.get('campaign_goal', 'Brand awareness')}

Looking at the image and all context above, produce a JSON response (no markdown fences):
{{
  "quote": "The hero campaign phrase — max 12 words, memorable and on-brand",
  "cta": "A compelling call-to-action button text (max 5 words)",
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5"],
  "ad_copy_short": "Social media caption variant — punchy, max 30 words",
  "ad_copy_long": "Email/landing page copy — 2 sentences, sophisticated",
  "justification": "1-2 sentences on why this copy fits the image and trend"
}}
""",
                },
            ],
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {"quote": raw[:100], "justification": ""}

    _log("done", f"🎯 Quote: **{parsed.get('quote', '')}**")

    return parsed