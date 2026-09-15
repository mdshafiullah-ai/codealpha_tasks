# E-Commerce FAQ Chatbot

A Python FAQ chatbot built with Streamlit that answers customer questions using classical NLP — no LLM or external API required.

## How It Works

```
User Question → NLTK Preprocessing → TF-IDF Vectorization → Cosine Similarity → FAQ Retrieval → Answer
```

1. **NLTK preprocessing** — lowercase, tokenization, stopword removal
2. **TF-IDF** — vectorize FAQ questions and user input with scikit-learn
3. **Cosine similarity** — find the closest FAQ match
4. **Threshold check** — return the answer or a fallback for unrelated questions

## Project Structure

```
CodeAlpha-FAQ-Chatbot/
├── app.py              # Streamlit chat UI
├── faq_data.json       # 45 e-commerce FAQ entries
├── requirements.txt
├── README.md
└── src/
    └── nlp_utils.py    # Preprocessing and matching logic
```

## Setup

```bash
pip install -r requirements.txt
```

NLTK data (`punkt`, `stopwords`) is downloaded automatically on first run.

## Run

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

## Features

- Chat UI with `st.chat_message()` and `st.chat_input()`
- Matched **category** and **similarity score** shown with each answer
- Adjustable similarity threshold in the sidebar
- **Clear chat** button to reset conversation history
- Fallback message when no FAQ meets the confidence threshold

## Example Questions

- "How long does shipping take?"
- "Can I return an item?"
- "What payment methods do you accept?"
- "How do I track my order?"
- "Do you ship internationally?"

## Tech Stack

- Python 3.10+
- Streamlit
- NLTK
- scikit-learn (TF-IDF + cosine similarity)
- NumPy
