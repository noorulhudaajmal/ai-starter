import sys
import threading
from pathlib import Path
from queue import Queue, Empty

import streamlit as st

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from db import get_categories, get_products, get_product_by_id, save_campaign, get_campaigns
from agents import run_campaign

# Page config
st.set_page_config(
    page_title="Campaign Studio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# css
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --ink: #0d0d0d;
  --paper: #faf9f6;
  --cream: #f2efe8;
  --gold: #c9a84c;
  --gold-light: #e8d5a3;
  --gold-pale: #fdf8ec;
  --sage: #6b7c6e;
  --muted: #8a8580;
  --card-bg: #fffdf8;
  --border: #e4e0d8;
  --border-dark: #ccc8be;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--cream);
    color: var(--ink);
}

/* force Streamlit's own wrappers to match */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--cream) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2.5rem 3rem; max-width: 1440px; }

/*  Masthead  */
.masthead {
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 0.75rem;
    margin-bottom: 1.8rem;
}
.masthead-logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
}
.masthead-dot { width:5px; height:5px; background:var(--gold); border-radius:50%; flex-shrink:0; }
.masthead-sub {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--muted);
    font-weight: 500;
}
.masthead-spacer { flex: 1; }

/*  Step labels  */
.step-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1rem;
}
.step-chip {
    background: var(--ink);
    color: #fff;
    font-size: 0.58rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
}
.step-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 600;
    line-height: 1;
}
.step-count {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--muted);
}

/*  Product card  */
.product-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 1.1rem 1rem 0.9rem;
    transition: border-color 0.18s, box-shadow 0.18s;
    cursor: pointer;
    min-height: 130px;
}
.product-card:hover { border-color: var(--gold); box-shadow: 0 3px 16px rgba(201,168,76,0.13); }
.product-card.selected {
    border-color: var(--gold);
    background: var(--gold-pale);
    box-shadow: 0 0 0 3px var(--gold-light);
}
.product-sku {
    font-size: 0.58rem; letter-spacing: 0.16em;
    color: var(--muted); text-transform: uppercase; margin-bottom: 0.25rem;
}
.product-name {
    font-family: 'Playfair Display', serif;
    font-size: 0.92rem; font-weight: 600;
    margin-bottom: 0.2rem; line-height: 1.3;
}
.product-brand { font-size: 0.72rem; color: var(--sage); font-weight: 500; margin-bottom: 0.55rem; }
.product-price { font-size: 1.05rem; font-weight: 600; }
.stock-badge {
    display: inline-block;
    font-size: 0.56rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    padding: 2px 7px; border-radius: 20px; margin-left: 0.4rem;
}
.stock-ok  { background:#e8f5e9; color:#2e7d32; }
.stock-low { background:#fff8e1; color:#f57f17; }

/*  Launch strip  */
.launch-strip {
    background: var(--ink);
    border-radius: 6px;
    padding: 1.1rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 2.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.launch-field-label {
    font-size: 0.56rem; text-transform: uppercase;
    letter-spacing: 0.18em; color: var(--gold);
    margin-bottom: 0.12rem; font-weight: 600;
}
.launch-field-value { font-size: 0.88rem; font-weight: 500; color: #fff; }

/*  Empty state  */
.empty-state {
    background: var(--cream);
    border: 1px dashed var(--border-dark);
    border-radius: 5px;
    padding: 1rem 1.4rem;
    color: var(--muted);
    font-size: 0.84rem;
    margin-bottom: 1rem;
}

/*  Campaign log  */
.log-entry {
    border-left: 3px solid var(--gold);
    padding: 0.5rem 1rem;
    margin: 0.3rem 0;
    background: var(--cream);
    border-radius: 0 4px 4px 0;
    font-size: 0.81rem;
}
.log-phase {
    border-left-color: var(--ink);
    background: #ede9df;
    font-weight: 600;
    font-size: 0.87rem;
}

/*  Results  */
.quote-display {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem; font-style: italic;
    line-height: 1.45; color: var(--ink);
    text-align: center;
    padding: 1.8rem 1.2rem;
    border-top: 2px solid var(--ink);
    border-bottom: 2px solid var(--ink);
    margin: 1rem 0 0.5rem;
}
.tagline-display {
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.22em; color: var(--gold);
    text-align: center; margin-bottom: 0.5rem;
}
.result-section {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 1rem;
}
.section-label {
    font-size: 0.6rem; text-transform: uppercase;
    letter-spacing: 0.2em; color: var(--gold);
    font-weight: 600; margin-bottom: 0.4rem; display: block;
}
.hashtag {
    display: inline-block;
    background: var(--cream); border: 1px solid var(--border);
    border-radius: 20px; padding: 2px 10px;
    font-size: 0.77rem; color: var(--sage); margin: 2px;
}
.cta-badge {
    display: inline-block;
    background: var(--ink); color: #fff;
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 15px; border-radius: 2px;
}

/*  Buttons  */
div[data-testid="stButton"] > button {
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: var(--ink) !important;
    color: #fff !important;
    border: none !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover:not(:disabled) {
    background: var(--gold) !important;
}
div[data-testid="stButton"] > button:disabled { opacity: 0.35 !important; }

/*  History  */
.history-item {
    display: flex; justify-content: space-between;
    align-items: flex-start; padding: 0.8rem 0;
    border-bottom: 1px solid var(--border); gap: 1rem;
}
.history-meta { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
.history-date { font-size: 0.68rem; color: var(--muted); white-space: nowrap; }
</style>
""", unsafe_allow_html=True)

#  Session defaults 
for key, val in {
    "selected_product_id": None,
    "campaign_result": None,
    "log_entries": [],
    "running": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

#  Masthead
st.markdown("""
<div class="masthead">
  <span class="masthead-logo">Marketing Assistant</span>
  <div class="masthead-dot"></div>
  <span class="masthead-sub">AI Campaign Studio</span>
  <div class="masthead-spacer"></div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_studio, tab_history = st.tabs(["📐  Campaign Studio", "📋  Campaign History"])



# STUDIO TAB
with tab_studio:

    #  Load categories 
    categories = get_categories()
    cat_labels = [f"{c['icon']} {c['name']}" for c in categories]

    #  Step 1: Campaign filters 
    st.markdown(
        '<div class="step-header">'
        '<span class="step-chip">Step 1</span>'
        '<span class="step-title">Configure Campaign</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        campaign_goal = st.selectbox(
            "Campaign Goal",
            ["Brand Awareness", "Product Launch", "Seasonal Sale", "Influencer Push", "Restock Alert"],
            index=0,
        )
    with c2:
        tone = st.selectbox(
            "Brand Tone",
            ["Modern & Aspirational", "Playful & Energetic", "Luxury & Refined", "Minimalist & Clean", "Bold & Edgy"],
            index=0,
        )
    with c3:
        audience = st.selectbox(
            "Audience",
            ["All", "Men", "Women", "Kids", "Teens", "Adults", "Seniors"],
            index=0,
        )
    with c4:
        selected_cat_label = st.selectbox(
            "Product Category",
            cat_labels,
            index=0,
        )

    # Resolve category
    selected_cat_name = selected_cat_label.split(" ", 1)[1]
    selected_cat      = next((c for c in categories if c["name"] == selected_cat_name), None)
    selected_cat_id   = selected_cat["id"] if selected_cat else None
    cat_icon          = selected_cat["icon"] if selected_cat else "📦"

    # Map audience → DB filters
    gender_filter    = audience if audience in ("Men", "Women", "Unisex") else None
    age_group_filter = audience if audience in ("Kids", "Teens", "Adults", "Seniors") else None

    filters = {
        "gender":        gender_filter or "All",
        "age_group":     age_group_filter or "All",
        "season":        "All",
        "campaign_goal": campaign_goal,
        "tone":          tone,
        "caption_style": "short and punchy",
    }

    st.markdown("<hr style='margin:0.3rem 0 1.5rem;border-color:#e4e0d8'>", unsafe_allow_html=True)

    #  Step 2: Product selection 
    products = get_products(
        category_id=selected_cat_id,
        gender=gender_filter,
        age_group=age_group_filter,
        min_stock=1,
    )

    # Clear stale selection when category/audience changes
    if st.session_state.selected_product_id:
        if st.session_state.selected_product_id not in {p["id"] for p in products}:
            st.session_state.selected_product_id = None
            st.session_state.campaign_result = None
            st.session_state.log_entries = []

    step2_count = f"{len(products)} product{'s' if len(products) != 1 else ''} available"
    st.markdown(
        f'<div class="step-header">'
        f'<span class="step-chip">Step 2</span>'
        f'<span class="step-title">{cat_icon} Select a {selected_cat_name} Product</span>'
        f'<span class="step-count">{step2_count}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not products:
        st.markdown(
            f'<div class="empty-state">No {selected_cat_name} products match the selected audience. '
            f'Try changing the <strong>Audience</strong> filter above.</div>',
            unsafe_allow_html=True,
        )
    else:
        COLS = 4
        for row_start in range(0, len(products), COLS):
            row_products = products[row_start : row_start + COLS]
            cols = st.columns(COLS)
            for col, prod in zip(cols, row_products):
                with col:
                    is_sel    = st.session_state.selected_product_id == prod["id"]
                    sel_cls   = "selected" if is_sel else ""
                    stock     = prod.get("stock", 0)
                    stock_cls = "stock-ok" if stock > 20 else "stock-low"

                    st.markdown(f"""
                    <div class="product-card {sel_cls}">
                        <div class="product-sku">{prod['sku']}</div>
                        <div class="product-name">{prod['name']}</div>
                        <div class="product-brand">{prod.get('brand','')}</div>
                        <div>
                            <span class="product-price">${prod['price']:.0f}</span>
                            <span class="stock-badge {stock_cls}">{stock} in stock</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    btn_label = "✓ Selected" if is_sel else "Select"
                    btn_type  = "primary" if is_sel else "secondary"
                    if st.button(btn_label, key=f"sel_{prod['id']}_{prod['stock']}", type=btn_type, use_container_width=True):
                        st.session_state.selected_product_id = prod["id"]
                        st.session_state.campaign_result = None
                        st.session_state.log_entries = []
                        st.rerun()

    #  Step 3: Launch 
    st.markdown("<hr style='margin:1.5rem 0 1rem;border-color:#e4e0d8'>", unsafe_allow_html=True)

    has_product = st.session_state.selected_product_id is not None
    product     = get_product_by_id(st.session_state.selected_product_id) if has_product else None

    st.markdown(
        '<div class="step-header">'
        '<span class="step-chip">Step 3</span>'
        '<span class="step-title">Launch Campaign</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if not has_product:
        st.markdown(
            '<div class="empty-state">← Select a product above to enable the campaign launch.</div>',
            unsafe_allow_html=True,
        )
        launch = False
    else:
        desc_snip = (product.get("description") or "")[:88]
        ellipsis  = "…" if len(product.get("description") or "") > 88 else ""
        st.markdown(f"""
        <div class="launch-strip">
            <div>
                <div class="launch-field-label">Product</div>
                <div class="launch-field-value">{product['name']}</div>
                <div style="font-size:0.7rem;color:#999;margin-top:2px">{desc_snip}{ellipsis}</div>
            </div>
            <div>
                <div class="launch-field-label">Goal</div>
                <div class="launch-field-value">{campaign_goal}</div>
            </div>
            <div>
                <div class="launch-field-label">Tone</div>
                <div class="launch-field-value">{tone}</div>
            </div>
            <div>
                <div class="launch-field-label">Audience</div>
                <div class="launch-field-value">{audience}</div>
            </div>
            <div>
                <div class="launch-field-label">Price</div>
                <div class="launch-field-value">${product['price']:.2f}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        _, btn_col = st.columns([4, 1])
        with btn_col:
            btn_text = "⏳  Running…" if st.session_state.running else "🚀  Run Campaign"
            launch = st.button(
                btn_text,
                type="primary",
                disabled=st.session_state.running,
                use_container_width=True,
            )

    #  Log display (between runs) 
    if st.session_state.log_entries:
        for entry in st.session_state.log_entries:
            cls = "log-phase" if entry["step"] == "phase" else "log-entry"
            st.markdown(f'<div class="{cls}">{entry["data"]}</div>', unsafe_allow_html=True)

    #  Execute pipeline 
    if has_product and launch and not st.session_state.running:
        st.session_state.running = True
        st.session_state.log_entries = []
        st.session_state.campaign_result = None

        log_placeholder = st.empty()
        progress_bar    = st.progress(0, text="Initialising agents…")
        log_queue       = Queue()

        def _cb(step, data):
            log_queue.put({"step": step, "data": data})

        def _run():
            try:
                res = run_campaign(product, filters, stream_callback=_cb)
                log_queue.put({"step": "__done__", "data": res})
            except Exception as exc:
                log_queue.put({"step": "__error__", "data": str(exc)})

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        phases    = ["Market Research", "Visual Design", "Copywriting", "Packaging"]
        phase_idx = 0
        all_logs  = []

        while thread.is_alive() or not log_queue.empty():
            try:
                msg = log_queue.get(timeout=0.3)
            except Empty:
                continue

            step = msg["step"]

            if step == "__done__":
                st.session_state.campaign_result = msg["data"]
                progress_bar.progress(100, text="✅  Campaign complete!")
                save_campaign({
                    "name":          f"{product['name']} — {campaign_goal}",
                    "product_id":    product["id"],
                    "status":        "complete",
                    "trend_summary": msg["data"].get("trend_summary", ""),
                    "caption":       msg["data"].get("caption", ""),
                    "tagline":       msg["data"].get("tagline", ""),
                    "quote":         msg["data"].get("quote", ""),
                    "image_path":    msg["data"].get("image_path", ""),
                    "report_path":   msg["data"].get("report_path", ""),
                    "filters":       filters,
                })
                break
            elif step == "__error__":
                st.error(f"❌  {msg['data']}")
                break
            elif step == "phase":
                phase_idx = min(phase_idx + 1, 4)
                progress_bar.progress(int(phase_idx / 4 * 90), text=f"{phases[min(phase_idx-1,3)]}…")
                all_logs.append({"step": step, "data": msg["data"]})
            else:
                all_logs.append({"step": step, "data": msg["data"]})

            with log_placeholder.container():
                for entry in all_logs[-14:]:
                    cls = "log-phase" if entry["step"] == "phase" else "log-entry"
                    st.markdown(f'<div class="{cls}">{entry["data"]}</div>', unsafe_allow_html=True)

        st.session_state.log_entries = all_logs
        st.session_state.running = False
        st.rerun()

    #  Results 
    result = st.session_state.campaign_result
    if result:
        st.markdown("<hr style='margin:1.5rem 0;border-color:#e4e0d8'>", unsafe_allow_html=True)
        st.markdown(
            '<div class="step-header">'
            '<span class="step-chip">Results</span>'
            '<span class="step-title">Campaign Assets</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        col_img, col_copy = st.columns([1, 1], gap="large")

        with col_img:
            image_path = result.get("image_path", "")
            if image_path and Path(image_path).exists():
                st.image(image_path, use_container_width=True)
            st.markdown(f"""
            <div class="quote-display">"{result.get('quote','')}"</div>
            <div class="tagline-display">{result.get('tagline','')}</div>
            """, unsafe_allow_html=True)

        with col_copy:
            st.markdown('<div class="result-section">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">Caption</span>', unsafe_allow_html=True)
            st.markdown(result.get("caption", ""))
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="result-section">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">Call to Action</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="cta-badge">{result.get("cta","Shop Now")}</span>', unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<span class="section-label">Hashtags</span>', unsafe_allow_html=True)
            tags_html = " ".join(f'<span class="hashtag">{h}</span>' for h in result.get("hashtags", []))
            st.markdown(tags_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="result-section">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">Ad Copy — Social</span>', unsafe_allow_html=True)
            st.markdown(result.get("ad_copy_short", ""))
            st.markdown('<span class="section-label" style="margin-top:1rem;display:block">Ad Copy — Email</span>', unsafe_allow_html=True)
            st.markdown(result.get("ad_copy_long", ""))
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📊  Full Market Research Summary", expanded=False):
            st.markdown(result.get("trend_summary", ""))

        report_path = result.get("report_path", "")
        if report_path and Path(report_path).exists():
            with open(report_path, "r") as f:
                report_md = f.read()
            st.download_button(
                "⬇️  Download Campaign Report",
                report_md,
                file_name=Path(report_path).name,
                mime="text/markdown",
                type="primary",
            )



# HISTORY TAB
with tab_history:
    st.markdown(
        '<div class="step-header">'
        '<span class="step-chip">Archive</span>'
        '<span class="step-title">Campaign History</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    campaigns = get_campaigns()
    if not campaigns:
        st.info("No campaigns yet. Launch your first campaign in the Studio tab.")
    else:
        for cam in campaigns:
            icon = cam.get("category_icon", "🛍️")
            c1, c2 = st.columns([5, 1])
            with c1:
                quote_line = (
                    f'<div style="font-style:italic;font-size:0.82rem;margin-top:4px;color:#555">"{cam["quote"]}"</div>'
                    if cam.get("quote") else ""
                )
                st.markdown(f"""
                <div class="history-item">
                    <div>
                        <div style="font-weight:600;font-size:0.92rem">
                            {icon}&nbsp; {cam['name']}
                        </div>
                        <div class="history-meta">{cam.get('product_name','')} · {cam.get('status','').title()}</div>
                        {quote_line}
                    </div>
                    <span class="history-date">{cam['created_at'][:10]}</span>
                </div>""", unsafe_allow_html=True)
            with c2:
                rp = cam.get("report_path", "")
                if rp and Path(rp).exists():
                    with open(rp, "r") as f:
                        st.download_button(
                            "⬇ Report", f.read(),
                            file_name=Path(rp).name,
                            mime="text/markdown",
                            key=f"dl_{cam['id']}",
                            use_container_width=True,
                        )