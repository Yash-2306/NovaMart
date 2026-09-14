"""
Lightweight RAG layer over refund_policy.md using BM25 keyword search.

Chunks the policy by section headings (##), indexes them using BM25, and
retrieves the most relevant chunks based on exact term matching.
"""

from __future__ import annotations

import math
from pathlib import Path
import re
import structlog

logger = structlog.get_logger()


class BM25:
    """
    BM25 implementation for text retrieval.
    Matches query terms against document terms using TF-IDF and length normalization.
    """
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.corpus_size = len(corpus)
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.nd = {}  # term -> number of docs containing the term
        
        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            
            # Count term frequencies in this document
            freqs = {}
            for token in tokens:
                freqs[token] = freqs.get(token, 0) + 1
            self.doc_term_freqs.append(freqs)
            
            # Increment document count for each unique term
            for token in freqs:
                self.nd[token] = self.nd.get(token, 0) + 1
                
        self.avg_doc_length = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0
        
        # Precompute IDF for terms in corpus.
        # Standard BM25 IDF: ln((N - n(q) + 0.5) / (n(q) + 0.5) + 1.0)
        self.idf = {}
        for term, freq in self.nd.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer that converts text to lowercase and extracts word/number tokens."""
        text = text.lower()
        return re.findall(r'\b[a-z0-9]+\b', text)

    def get_scores(self, query: str) -> list[float]:
        """Calculate BM25 scores for each document against the query."""
        query_tokens = self._tokenize(query)
        scores = []
        
        for doc_idx in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_lengths[doc_idx]
            freqs = self.doc_term_freqs[doc_idx]
            
            for token in query_tokens:
                if token not in self.idf:
                    continue
                f = freqs.get(token, 0)
                idf = self.idf[token]
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
                score += idf * (numerator / denominator)
            scores.append(score)
            
        return scores


# Module-level state to match original rag.py public interface
_searcher: BM25 | None = None
_chunks: list[str] = []


def _get_policy_path() -> Path:
    """Resolve the path to refund_policy.md."""
    # Try relative to this file first, then common locations
    candidates = [
        Path(__file__).parent.parent / "data" / "refund_policy.md",
        Path("/app/app/data/refund_policy.md"),
        Path("app/data/refund_policy.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("refund_policy.md not found in any expected location")


def _split_into_chunks(text: str) -> list[str]:
    """Split policy document into chunks by ## section headings."""
    sections: list[str] = []
    current_section: list[str] = []

    for line in text.split("\n"):
        if line.startswith("## ") and current_section:
            sections.append("\n".join(current_section).strip())
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section).strip())

    # Filter out empty chunks and the title chunk if it's just the header
    return [s for s in sections if len(s.strip()) > 20]


def initialize_rag() -> None:
    """
    Load the policy document, split into chunks, index with BM25.
    Called once at application startup.
    """
    global _searcher, _chunks

    logger.info("rag_initializing", model="BM25-pure-python")

    # Load and chunk policy
    policy_path = _get_policy_path()
    policy_text = policy_path.read_text(encoding="utf-8")
    _chunks = _split_into_chunks(policy_text)

    logger.info("rag_chunks_created", count=len(_chunks))

    # Initialize BM25 searcher
    _searcher = BM25(_chunks)

    logger.info("rag_initialized", chunks=len(_chunks), search_type="BM25")


def retrieve_policy_context(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieve the top_k most relevant policy sections for a given query using BM25.

    Args:
        query: The search query (e.g., "final sale return policy")
        top_k: Number of sections to retrieve (default: 3)

    Returns:
        List of the most relevant policy sections as strings.
    """
    if _searcher is None or not _chunks:
        logger.warning("rag_not_initialized", action="returning_all_chunks")
        return _chunks[:top_k] if _chunks else ["No policy document loaded."]

    # Compute BM25 scores
    scores = _searcher.get_scores(query)

    # Get top_k indices sorted by score descending, with original index as secondary key
    # to maintain stable sorting/tie-breaking.
    indexed_scores = list(enumerate(scores))
    indexed_scores.sort(key=lambda x: (x[1], -x[0]), reverse=True)
    top_indices = [idx for idx, score in indexed_scores[:top_k]]

    results = [_chunks[i] for i in top_indices]

    logger.debug(
        "rag_query",
        query=query[:100],
        top_scores=[float(scores[i]) for i in top_indices],
    )

    return results
