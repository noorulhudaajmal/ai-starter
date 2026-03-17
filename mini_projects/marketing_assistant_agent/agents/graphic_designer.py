import json
import os
import re
from io import BytesIO
from pathlib import Path

import openai
import requests
from PIL import Image

import openai

from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)



def graphic_designer_agent(
    product: dict,
    trend_summary: str,
    filters: dict,
    stream_callback=None,
) -> dict:
    """
    Generates a campaign image, visual prompt, and caption.

    Returns:
        dict: image_path, image_url, prompt, caption
    """



    def _log(step, data):
        if stream_callback:
            stream_callback(step, data)

    tone = filters.get("tone", "modern and aspirational")
    season = filters.get("season", "Summer")
    gender = filters.get("gender", "Unisex")
    caption_style = filters.get("caption_style", "short and punchy")

    _log("start", "🎨 Graphic Designer Agent crafting visual concept...")

    # Step 1: Generate visual prompt + caption via cheap model
    system_msg = (
        "You are a luxury brand visual director. You craft cinematic image generation prompts "
        "and marketing captions that feel editorial and aspirational."
    )
    user_msg = f"""
Product: {product['name']}
Description: {product.get('description', '')}
Image hint: {product.get('image_hint', '')}
Trend insights: {trend_summary[:800]}
Tone: {tone}
Season: {season}
Target: {gender}
Caption style: {caption_style}

Output ONLY valid JSON (no markdown fences) in this exact format:
{{
  "prompt": "A highly detailed, cinematic scene for DALL-E 3 (max 800 chars)",
  "caption": "Marketing caption in the requested style (max 20 words)",
  "tagline": "A memorable brand tagline for this campaign (max 8 words)"
}}
"""

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {}

    prompt = parsed.get("prompt", f"A professional campaign image for {product['name']}")
    caption = parsed.get("caption", product["name"])
    tagline = parsed.get("tagline", "")

    _log("prompt_ready", f"✏️ Visual prompt crafted ({len(prompt)} chars)")
    _log("caption_ready", f"💬 Caption: **{caption}**")

    # Step 2: Generate image via DALL-E 3
    _log("generating_image", "🖼 Generating campaign image with DALL-E 3...")

    image_response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="url",
    )

    image_url = image_response.data[0].url

    # Step 3: Save locally
    img_bytes = requests.get(image_url, timeout=30).content
    img = Image.open(BytesIO(img_bytes))

    sku = product.get("sku", "product").replace("-", "_").lower()
    filename = f"campaign_{sku}_{int(__import__('time').time())}.png"
    image_path = OUTPUT_DIR / filename
    img.save(image_path)

    _log("image_saved", f"💾 Image saved → `{image_path}`")

    return {
        "image_url": image_url,
        "image_path": str(image_path),
        "prompt": prompt,
        "caption": caption,
        "tagline": tagline,
    }