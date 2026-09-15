"""NLP utilities for FAQ matching: preprocessing, TF-IDF, and cosine similarity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def ensure_nltk_data() -> None:
    """Download required NLTK corpora if not already present."""
    resources = (
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
    )
    for lookup_path, download_name in resources:
        try:
            nltk.data.find(lookup_path)
        except LookupError:
            nltk.download(download_name, quiet=True)


def preprocess_text(text: str) -> str:
    """
    Preprocess text: lowercase, tokenize, remove stopwords and non-alphanumeric tokens.

    Returns a space-joined string of cleaned tokens for TF-IDF vectorization.
    """
    ensure_nltk_data()

    text = text.lower().strip()
    tokens = word_tokenize(text)
    stops = set(stopwords.words("english"))

    cleaned = [
        token
        for token in tokens
        if token.isalnum() and token not in stops and len(token) > 1
    ]
    return " ".join(cleaned)


class FAQEntry(NamedTuple):
    id: int
    category: str
    question: str
    answer: str


class MatchResult(NamedTuple):
    faq: FAQEntry | None
    similarity: float
    matched: bool


class FAQMatcher:
    """Match user questions to FAQs using TF-IDF and cosine similarity."""

    def __init__(self, faqs: list[FAQEntry], similarity_threshold: float = 0.25):
        self.faqs = faqs
        self.similarity_threshold = similarity_threshold

        corpus = [preprocess_text(faq.question) for faq in faqs]
        self._vectorizer = TfidfVectorizer()
        self._faq_matrix = self._vectorizer.fit_transform(corpus)

    def match(self, user_question: str) -> MatchResult:
        """Find the best matching FAQ for a user question."""
        processed = preprocess_text(user_question)
        if not processed.strip():
            return MatchResult(faq=None, similarity=0.0, matched=False)

        query_vector = self._vectorizer.transform([processed])
        similarities = cosine_similarity(query_vector, self._faq_matrix).flatten()
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= self.similarity_threshold:
            return MatchResult(
                faq=self.faqs[best_idx],
                similarity=best_score,
                matched=True,
            )

        return MatchResult(faq=None, similarity=best_score, matched=False)


def load_faqs(path: str | Path) -> list[FAQEntry]:
    """Load FAQ entries from a JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return [
        FAQEntry(
            id=item["id"],
            category=item["category"],
            question=item["question"],
            answer=item["answer"],
        )
        for item in data
    ]
