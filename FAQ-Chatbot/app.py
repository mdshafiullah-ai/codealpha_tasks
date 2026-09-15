"""Streamlit FAQ chatbot using NLTK preprocessing, TF-IDF, and cosine similarity."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.nlp_utils import FAQMatcher, load_faqs  # noqa: E402

FAQ_PATH = ROOT / "faq_data.json"
DEFAULT_THRESHOLD = 0.25

FALLBACK_MESSAGE = (
    "I'm sorry, I couldn't find a close match for your question. "
    "Please try rephrasing or contact our support team at support@shopstore.com "
    "or call 1-800-555-0199."
)


@st.cache_resource
def get_matcher(threshold: float) -> FAQMatcher:
    faqs = load_faqs(FAQ_PATH)
    return FAQMatcher(faqs, similarity_threshold=threshold)


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def clear_chat() -> None:
    st.session_state.messages = []


def format_assistant_reply(result) -> str:
    if not result.matched or result.faq is None:
        score_pct = result.similarity * 100
        return (
            f"{FALLBACK_MESSAGE}\n\n"
            f"_Best match confidence: {score_pct:.1f}% (below threshold)_"
        )

    score_pct = result.similarity * 100
    return (
        f"{result.faq.answer}\n\n"
        f"---\n"
        f"**Category:** {result.faq.category}  \n"
        f"**Similarity score:** {score_pct:.1f}%"
    )


def main() -> None:
    st.set_page_config(
        page_title="E-Commerce FAQ Chatbot",
        page_icon="💬",
        layout="centered",
    )

    init_session_state()

    st.title("E-Commerce FAQ Assistant")
    st.caption(
        "Ask about shipping, returns, payments, orders, and more. "
        "Answers are retrieved from our FAQ knowledge base using NLP matching."
    )

    with st.sidebar:
        st.header("Settings")
        threshold = st.slider(
            "Similarity threshold",
            min_value=0.10,
            max_value=0.60,
            value=DEFAULT_THRESHOLD,
            step=0.05,
            help="Minimum cosine similarity required to return an FAQ answer.",
        )
        st.divider()
        if st.button("Clear chat", use_container_width=True):
            clear_chat()
            st.rerun()

        st.divider()
        st.markdown("**How it works**")
        st.markdown(
            "1. NLTK preprocessing (lowercase, tokenize, stopwords)\n"
            "2. TF-IDF vectorization\n"
            "3. Cosine similarity matching\n"
            "4. Best FAQ answer retrieval"
        )

    matcher = get_matcher(threshold)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about our store..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        result = matcher.match(prompt)
        reply = format_assistant_reply(result)

        st.session_state.messages.append({"role": "assistant", "content": reply})

        with st.chat_message("assistant"):
            st.markdown(reply)


if __name__ == "__main__":
    main()
