"""
app_streamlit.py
-----------------
Web interface for the agentic store assistant (bonus deliverable).

Run with:
    streamlit run app_streamlit.py

What makes this feel "agentic" rather than a plain Q&A box:
- A live "Agent reasoning" panel (st.status) that streams each tool call
  as the agent makes it -- e.g. "Looking up order ORD-1001" -> "Found it,
  searching for alternatives" -> "Done". This makes the autonomous
  tool-selection and tool-chaining visible in real time, which is the
  actual point of the assignment.
- A badge showing which "brain" is answering (Gemini / Claude / rule-based
  fallback), so it's obvious whether the LLM is configured.
- Sample questions as clickable cards in the sidebar.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from dotenv import load_dotenv
load_dotenv()

from agent.agent_core import run_agent
from agent import logger as agent_logger


st.set_page_config(page_title="Store Assistant", page_icon="🛍️", layout="centered")

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; max-width: 760px; }

        .hero {
            background: linear-gradient(135deg, #0F6E56 0%, #085041 100%);
            color: white;
            padding: 1.75rem 2rem;
            border-radius: 14px;
            margin-bottom: 1.5rem;
        }
        .hero h1 { margin: 0; font-size: 1.6rem; }
        .hero p { margin: 0.4rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }

        .brain-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .brain-llm { background: #E1F5EE; color: #085041; }
        .brain-fallback { background: #FAEEDA; color: #633806; }

        div[data-testid="stSidebar"] button {
            text-align: left;
            border-radius: 10px !important;
        }

        .step-line {
            font-size: 0.88rem;
            padding: 2px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _active_provider() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return "llm", "Gemini is reasoning over your question"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "llm", "Claude is reasoning over your question"
    return "fallback", "Rule-based fallback (no API key configured)"


def _describe_call(tool_name: str, tool_input: dict, tool_output) -> tuple:
    """Returns (in_progress_text, result_text) for a friendly live trace."""
    if tool_name == "get_order":
        oid = tool_input.get("order_id", "?")
        in_progress = f"Looking up order **{oid}**"
        result = "Order found" if tool_output else f"No order found with ID {oid}"
    elif tool_name == "get_product":
        pid = tool_input.get("product_id", "?")
        in_progress = f"Fetching product **{pid}**"
        result = f"Found: {tool_output['name']}" if tool_output else f"No product found with ID {pid}"
    elif tool_name == "search_products":
        q = tool_input.get("query", "")
        in_progress = f"Searching products for \u201c{q}\u201d"
        n = len(tool_output) if tool_output else 0
        result = f"Found {n} matching product(s)" if n else "No matching products found"
    else:
        in_progress = f"Calling {tool_name}"
        result = "Done"
    return in_progress, result


def _run_with_trace(question: str, status_box):
    """Runs the agent, writing a live step-by-step trace into status_box."""
    calls = []
    original_log = agent_logger.log_tool_call

    def spy(tool_name, tool_input, tool_output):
        in_progress, result = _describe_call(tool_name, tool_input, tool_output)
        status_box.write(f"🔎 {in_progress}")
        status_box.write(f"&nbsp;&nbsp;&nbsp;↳ {result}")
        calls.append({"tool": tool_name, "input": tool_input, "output": tool_output})
        return original_log(tool_name, tool_input, tool_output)

    agent_logger.log_tool_call = spy
    try:
        answer = run_agent(question)
    finally:
        agent_logger.log_tool_call = original_log

    return answer, calls


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🛍️ Store Assistant</h1>
        <p>An agent that decides which tools to call, chains them, and answers like a human support rep.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

mode, mode_text = _active_provider()
badge_class = "brain-llm" if mode == "llm" else "brain-fallback"
st.markdown(f'<span class="brain-badge {badge_class}">{mode_text}</span>', unsafe_allow_html=True)
st.write("")

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.subheader("Try a sample question")
    samples = [
        "Where is order ORD-1002?",
        "Is there a cheaper alternative to the shoes I ordered in ORD-1001?",
        "What's the status of ORD-9999?",
        "Do you have any electronics?",
        "Tell me about PRD-002",
    ]
    for s in samples:
        if st.button(s, use_container_width=True):
            st.session_state["pending_question"] = s

    st.divider()
    st.caption("**Available tools**")
    st.caption("🔎 `get_order` · 🔎 `search_products` · 🔎 `get_product`")
    st.caption("Set `GEMINI_API_KEY` in a `.env` file for free LLM-powered reasoning.")

# --------------------------------------------------------------------------
# Chat history + input
# --------------------------------------------------------------------------

if "history" not in st.session_state:
    st.session_state["history"] = []

for turn in st.session_state["history"]:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        if turn["calls"]:
            with st.expander(f"🧠 Agent reasoning ({len(turn['calls'])} tool call(s))"):
                for c in turn["calls"]:
                    in_progress, result = _describe_call(c["tool"], c["input"], c["output"])
                    st.markdown(f"**{in_progress}** \u2014 {result}")
        st.write(turn["answer"])

question = st.chat_input("Ask about an order, a product, or a cheaper alternative...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.status("Agent is reasoning...", expanded=True) as status_box:
            answer, calls = _run_with_trace(question, status_box)
            status_box.update(label="Reasoning complete", state="complete")
        st.write(answer)

    st.session_state["history"].append({"question": question, "answer": answer, "calls": calls})