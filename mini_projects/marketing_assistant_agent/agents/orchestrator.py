from .market_research import market_research_agent
from .graphic_designer import graphic_designer_agent
from .copywriter import copywriter_agent
from .packaging import packaging_agent


def run_campaign(product: dict, filters: dict, stream_callback=None) -> dict:
    """
    Full campaign pipeline:
      1. Market Research Agent
      2. Graphic Designer Agent
      3. Copywriter Agent
      4. Packaging Agent

    Args:
        product:  Product dict from DB.
        filters:  Campaign config (gender, age_group, season, tone, campaign_goal, caption_style).
        stream_callback: Optional callable(step, message) for real-time UI updates.

    Returns:
        dict with all campaign assets + report path.
    """

    def _log(step, data):
        if stream_callback:
            stream_callback(step, data)

    _log("phase", "📡 Phase 1 — Market Research")
    research = market_research_agent(product, filters, stream_callback=stream_callback)
    trend_summary = research["trend_summary"]

    _log("phase", "🎨 Phase 2 — Visual Design")
    visuals = graphic_designer_agent(product, trend_summary, filters, stream_callback=stream_callback)

    _log("phase", "✍️ Phase 3 — Copywriting")
    copy = copywriter_agent(
        product=product,
        image_path=visuals["image_path"],
        trend_summary=trend_summary,
        caption=visuals["caption"],
        tagline=visuals["tagline"],
        filters=filters,
        stream_callback=stream_callback,
    )

    _log("phase", "📦 Phase 4 — Packaging Report")
    report_path = packaging_agent(
        product=product,
        trend_summary=trend_summary,
        image_path=visuals["image_path"],
        caption=visuals["caption"],
        tagline=visuals["tagline"],
        quote=copy.get("quote", ""),
        cta=copy.get("cta", "Shop Now"),
        hashtags=copy.get("hashtags", []),
        ad_copy_short=copy.get("ad_copy_short", ""),
        ad_copy_long=copy.get("ad_copy_long", ""),
        justification=copy.get("justification", ""),
        filters=filters,
        stream_callback=stream_callback,
    )

    return {
        "trend_summary": trend_summary,
        "image_path": visuals["image_path"],
        "image_url": visuals.get("image_url", ""),
        "prompt": visuals["prompt"],
        "caption": visuals["caption"],
        "tagline": visuals["tagline"],
        "quote": copy.get("quote", ""),
        "cta": copy.get("cta", ""),
        "hashtags": copy.get("hashtags", []),
        "ad_copy_short": copy.get("ad_copy_short", ""),
        "ad_copy_long": copy.get("ad_copy_long", ""),
        "justification": copy.get("justification", ""),
        "report_path": report_path,
    }