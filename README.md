# Store Support Agent (Agentic AI)

A customer-support AI agent for a fictional online store. It reads a customer's question, decides which backend tool(s) to call, runs them (chaining more than one if needed), and replies in plain English — without inventing data it doesn't actually have.

**Live app:** https://agentic-ai-store-assistant-tahasjwtq4cahtuphti3cl.streamlit.app/
**Source code:** https://github.com/mahiwal619/agentic-ai-store-assistant

## The 3 tools the agent can call

| Tool | What it does |
|---|---|
| `get_order(order_id)` | Looks up an order's status, items, tracking number, delivery date |
| `search_products(query)` | Keyword search across the product catalog |
| `get_product(product_id)` | Looks up one product's price, stock, rating, description |

All three live in `agent/tools.py` and read from two local JSON files (`data/orders.json`, `data/products.json`) — there's no real store backend, this is mock data made for the assignment.

## How a question gets answered

This is the `run_agent(question)` function in `agent/agent_core.py`:

1. The question and the 3 tool definitions above are sent to **Google Gemini** (model: `gemini-2.5-flash`, free tier).
2. Gemini decides which tool to call first and with what input. The code runs that tool against the JSON data and sends the real result back to Gemini.
3. Gemini can ask for another tool call (this is how chaining happens — e.g. "find a cheaper shoe" first looks up the order, then searches the catalog) or give a final answer. This loop runs up to 5 times before giving up.
4. If no `GEMINI_API_KEY` is set, or the Gemini call fails for any reason, the code falls back to `agent/rule_based_router.py` — a simpler keyword/regex-based version that handles the same question types without needing any API. This means the app still works even with no key configured.
5. Every tool call (name, input, output) is logged to `logs/tool_calls.log` via `agent/logger.py`.

## Handling bad input

- Order ID or product ID that doesn't exist → the tool returns `None`, and the agent tells the customer it wasn't found, instead of guessing.
- Search with no matches → returns an empty list, agent says so honestly.
- A question with no order/product reference at all → the agent asks a clarifying question.

## What's in this repo

```
agent/
  tools.py               the 3 tools + helpers used by the UI to list orders/products
  agent_core.py           run_agent() -- the Gemini tool-calling loop + fallback logic
  rule_based_router.py    the no-API-key fallback
  logger.py               logs every tool call
data/
  orders.json              6 sample orders
  products.json            12 sample products
tests/
  test_agent.py            20 pytest tests for the tools, fallback router, and run_agent()
app_streamlit.py           the web UI (guided help-center style)
requirements.txt
.env.example                template showing what env variable to set
```

## Running it locally

```bash
pip install -r requirements.txt
cp .env.example .env
```
Then open `.env` and add a free Gemini key from https://aistudio.google.com/apikey, and run:
```bash
streamlit run app_streamlit.py
```

## Running the tests

```bash
python -m pytest tests/test_agent.py -v
```
20 tests, covering the 3 tools directly, the rule-based router's responses, and `run_agent()`'s fallback behavior when no API key is set.

## Tech used

Python, Google Gemini (`google-genai` SDK), Streamlit, pytest, python-dotenv.
