# Design Notes — Store Support Agent

## Why an LLM decides the tool calls, not a rulebook

The spec says the agent has to "decide which tool(s) to use" and "call them in the correct order." A simple if/else chain checking for keywords like "order" or "cheaper" can technically satisfy that, but it's not really deciding anything — it's just routing. So the main implementation, `run_agent()` in `agent_core.py`, sends the question along with the three tool definitions to Google Gemini and lets the model itself pick which function to call, what arguments to pass, and whether it needs to call another tool afterward based on the first result. That second part — calling a tool again based on what the first one returned — is the actual chaining behavior the assignment is testing for.

## The three tools and why they never raise errors

`get_order`, `search_products`, and `get_product` live in `tools.py`. None of them throw an exception when something isn't found — `get_order`/`get_product` return `None`, and `search_products` returns an empty list. The reasoning: if a tool *could* throw, then either the LLM has to handle a Python traceback (bad), or the calling code has to wrap every call in try/except and decide what to tell the customer anyway (which is what a clean `None` return already gives you, just without the exception machinery). It also makes the "don't fabricate data" requirement easy to enforce — there's no code path where a missing record needs to be guessed at.

## Two brains: Gemini, with a rule-based backup

`agent_core.py` checks for a `GEMINI_API_KEY` environment variable. If it's missing, or if the Gemini API call fails (bad key, no internet, rate limit), the agent calls `run_agent_rule_based()` instead — a separate file (`rule_based_router.py`) that uses regex to spot order IDs, product IDs, and phrases like "cheaper" or "do you have," then calls the exact same three tools manually. It's less impressive than genuine reasoning, but it means the app is never just broken. I'd rather it answer correctly without "real AI" than show an error screen.

Gemini specifically (not OpenAI or Claude) was picked because it's free without needing a card on file — important since this has to run on a mentor's machine, not just mine.

## The web interface

Streamlit wasn't required, but a free-text box assumes the user already knows valid order/product IDs, which defeats the point of a demo. Instead the UI works like a help-center menu — pick "track my order," then pick a real order from a list (pulled straight from `orders.json`), and the actual question text gets built automatically behind the scenes. There's a live status panel that prints out each tool call as it happens (e.g. "looking up order ORD-1002 → order found"), so the chaining behavior described above is actually visible instead of just a number arriving instantly.

## Tests

`test_agent.py` checks the three tools directly (valid/invalid IDs, empty search), checks the rule-based router's text responses for each question type, and checks that `run_agent()` correctly falls back to the rule-based path when no API key is present. All 20 tests run in well under a second since none of them touch the network.

## What this doesn't do

There's no memory across questions — every call to `run_agent()` is independent, matching the function signature the assignment specifies (`run_agent(question: str) -> str`). Typing "yes" after getting an answer won't make sense to the agent, because it has no idea what it would be agreeing to. Building conversation memory in would have been straightforward but wasn't part of what was asked for.
