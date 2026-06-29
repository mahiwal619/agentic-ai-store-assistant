# Store Support Agent — Agentic AI Assignment

A customer-support agent for a fictional online store. Given a plain-English question, it works out for itself which backend function(s) it needs, calls them (sometimes more than one, in sequence), and turns the result into a normal-sounding reply — without ever inventing facts it doesn't actually have.

**Try it live:** https://agentic-ai-store-assistant-tahasjwtq4cahtuphti3cl.streamlit.app/
**Source:** https://github.com/mahiwal619/agentic-ai-store-assistant

## The problem this solves

A customer might type something like *"Where's my order ORD-1002?"* or *"Is there anything cheaper than the shoes in ORD-1001?"*. The second one can't be answered with a single lookup — the agent first has to find out what was actually ordered, then go search for cheaper options in that category. That's the behavior this assignment is testing: can the agent figure out *on its own* that it needs two steps, not one, and execute them in the right order?

## The three functions it can call

| Function | What it returns |
|---|---|
| `get_order(order_id)` | Order status, items ordered, tracking number, delivery date |
| `search_products(query)` | A list of catalog products matching a keyword |
| `get_product(product_id)` | A single product's price, stock status, rating, description |

These live in `agent/tools.py` and read from two flat JSON files (`data/orders.json`: 6 sample orders, `data/products.json`: 12 sample products). There's no real database or store behind this — it's mock data built specifically for this assignment, and that's expected since the brief never provides a real backend.

## What actually happens when you ask a question

The entry point is `run_agent(question)` inside `agent/agent_core.py`. Step by step:

1. The raw question, along with descriptions of the three functions above, gets sent to **Google Gemini** (`gemini-2.5-flash`).
2. Gemini responds with which function it wants called and what arguments to use. The code runs that exact function against the real JSON data — it doesn't let Gemini make up the result.
3. The real result goes back to Gemini. At this point Gemini either asks for another function call (this is the chaining step) or writes a final answer in plain English.
4. That loop can repeat a few times before the code gives up and returns a generic "couldn't figure it out" message, as a safety net against infinite loops.

If `GEMINI_API_KEY` isn't set in the environment, or the call to Gemini fails for any reason — bad key, no internet, hit a rate limit — the code switches over to `agent/rule_based_router.py` instead. That file does the same job without any AI at all: it uses regex to spot things like an order ID pattern (`ORD-####`) or words like "cheaper," then calls the same three functions directly. It's a much dumber version of the same idea, but it means the project always produces *some* correct answer, even with zero internet access.

Gemini was chosen over OpenAI or Anthropic specifically because its API has a free tier that doesn't ask for a credit card — relevant since this has to actually run on a mentor's laptop, not just stay as a demo on one machine.

## How bad input is handled

- An order ID or product ID that doesn't exist in the data → the function returns `None`, and the agent says plainly that it couldn't find it. It does not guess a plausible-sounding status.
- A search with zero matching products → returns an empty list, and the agent says it found nothing rather than listing fake products.
- A question with no order/product reference at all (e.g. just "hello") → the agent asks what the customer needs instead of assuming.

## The interface

A free-text box only really works if you already know valid order IDs by heart, which isn't realistic for a demo. So `app_streamlit.py` is built as a guided menu instead — pick what you need ("track an order," "find something cheaper," etc.), then pick the actual item from a list pulled straight from the JSON data, and the corresponding question gets built and sent automatically. While the agent is working, a live panel prints out each function call as it happens (e.g. "looking up order ORD-1002 → found it"), so the multi-step chaining described above is something you can actually watch happen, not just a number that appears.

## Testing

`tests/test_agent.py` has 20 pytest tests. They check the three functions directly for valid/invalid IDs and empty searches, check that the rule-based fallback gives sensible text for each type of question, and check that `run_agent()` correctly drops into the fallback path when there's no API key available. None of the tests call the real Gemini API, so they run instantly and don't need any setup beyond `pip install pytest`.

## Stack

Python 3.13, `google-genai` (Gemini SDK), Streamlit, pytest, python-dotenv.

## Running this yourself

```bash
pip install -r requirements.txt
cp .env.example .env
```
Open `.env`, paste in a free Gemini key from https://aistudio.google.com/apikey, then:
```bash
streamlit run app_streamlit.py
```
It also runs fine with no key at all — you'll just get the rule-based answers instead of Gemini's.

To run the tests:
```bash
python -m pytest tests/test_agent.py -v
```

## What it deliberately doesn't do

`run_agent()` takes a single question and returns a single answer — it has no memory of earlier questions in the same session, because that's exactly the function signature the assignment specifies. So a follow-up like "yes" or "tell me more" right after an answer won't make sense to it; it gets treated as a brand new, unrelated question. Adding session memory would be a fairly small change, but it wasn't something the brief called for.

## More detail

- [`sample_io.md`](sample_io.md) — a table of real example questions and the agent's actual answers, with notes on what each one is meant to prove.
- [`DESIGN_DOC.md`](DESIGN_DOC.md) — the longer write-up of why things were built this way.
