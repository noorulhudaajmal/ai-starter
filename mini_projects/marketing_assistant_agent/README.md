# 🛍️ RetailMind : AI Campaign Studio

A production-grade multi-agent system that automates end-to-end marketing campaign creation for retail stores. Managers select a product from live inventory, configure campaign parameters, and four specialised AI agents collaborate to produce a full campaign package.

---

## Architecture

```
retail_campaign_agent/
├── main.py                  # for initial seed
├── requirements.txt
│
├── db/
│   ├── setup.py              # SQLite schema and seeder (28 products, 8 categories, 800 sales)
│   ├── queries.py            # Typed query helpers
│   └── __init__.py
│
├── tools/
│   ├── catalog.py            # Tool functions + LLM tool definitions
│   └── __init__.py
│
├── agents/
│   ├── market_research.py    # Trend research via web + catalog tools (agentic loop)
│   ├── graphic_designer.py   # Visual prompt + DALL-E 3 image generation
│   ├── copywriter.py         # Multimodal copy: quote, CTA, hashtags, ad variants
│   ├── packaging.py          # Executive markdown report assembly
│   └── __init__.py           # Orchestrator (run_campaign)
│
├─── app.py                # UI with real-time streaming logs
│
└── outputs/                  # Generated images + reports (auto-created)
```

---

## Agent Pipeline

```
User selects product + filters
         │
         ▼
┌─────────────────────┐
│  Market Research    │  gpt-4o-mini + tools (tavily web search, product catalog)
│  Agent              │  # trend_summary
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Graphic Designer   │  gpt-4o-mini -> creative brief -> DALL-E 3
│  Agent              │  # image_path, caption, tagline
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Copywriter         │  gpt-4o-mini (multimodal: image + trends)
│  Agent              │  # quote, CTA, hashtags, ad_copy_short, ad_copy_long
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Packaging          │  gpt-4o-mini -> polished executive brief
│  Agent              │  # campaign_report_{sku}.md
└─────────────────────┘
```

---

## Models Used (Cost-Optimised)

| Agent | Model | Rationale |
|---|---|---|
| Market Research | `gpt-4o-mini` | Tool-use, agentic loop, cheap |
| Graphic Designer | `gpt-4o-mini` + `dall-e-3` | Creative brief cheap; image necessary |
| Copywriter | `gpt-4o-mini` | Multimodal input supported |
| Packaging | `gpt-4o-mini` | Simple rewrite task |

---

## Database

SQLite with 6 tables:
- `categories` : 8 retail categories
- `products` : 28 products with SKU, brand, gender, age, season, tags, AI image hint
- `inventory` : stock levels with reorder thresholds
- `sales` : 800 synthetic sales transactions (last 12 months)
- `campaigns` : saved campaign results

---

## Setup

### 1. Clone & install
```bash
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
nano .env
# Edit .env with your keys
```

Required:
- `OPENAI_API_KEY`  for gpt-4o-mini + DALL-E 3
- `TAVILY_API_KEY`  for web trend search

### 3. Seed the database
```bash
python main.py --seed
```

### 4. Launch the UI
```bash
streamlit run app.py
```

---

## UI Features

- **Product Browser**  filterable by category, gender, age group, season, search
- **Campaign Configurator**  goal, tone, caption style
- **Real-time Streaming Logs**  watch each agent work live
- **Campaign Results**  image, quote, tagline, CTA, hashtags, ad copy variants
- **Downloadable Report**  full markdown campaign brief
- **Campaign History**  browse all past campaigns

---

## Extending

**Add a new agent:** Create `agents/social_scheduler.py`, add it to the pipeline in `agents/__init__.py`.

**Add new tools:** Define the function and its LLM schema in `tools/catalog.py`, add to `TOOL_DEFINITIONS` and `_TOOLS_MAP`.

**Switch models:** Change `model="openai:gpt-4o-mini"` to any aisuite-compatible model string (e.g. `anthropic:claude-haiku-4-5-20251001`).