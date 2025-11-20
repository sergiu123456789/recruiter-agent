# app/cv_rag.py
"""Cloud-Run safe CV RAG using Gemini embeddings (google-generativeai).

Production version:
- No debug prints
- Lazy embedding computation (first query)
- Top-K retrieval for better accuracy
- Tight prompt to reduce hallucinations
"""

from __future__ import annotations

from typing import List, Tuple, Optional
import os

import numpy as np
import google.generativeai as genai

EMBED_MODEL = "models/text-embedding-004"
GEN_MODEL = "gemini-1.5-flash"

_client_configured: bool = False
_rag: Optional["CVRAG"] = None


# -------------------------------------------------------------------
# Client config helpers
# -------------------------------------------------------------------


def _try_configure_client() -> bool:
    """Configure Gemini client once; return True if successful."""
    global _client_configured

    if _client_configured:
        return True

    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        return False

    try:
        genai.configure(api_key=key)
        _client_configured = True
        return True
    except Exception:
        return False


# -------------------------------------------------------------------
# CV loading + chunking
# -------------------------------------------------------------------


def _load_cv_text() -> str:
    base_dir = os.path.dirname(__file__)
    cv_path = os.path.join(base_dir, "cv.txt")

    if not os.path.exists(cv_path):
        raise FileNotFoundError(f"cv.txt not found at {cv_path}")

    with open(cv_path, "r", encoding="utf-8") as f:
        return f.read()


def _chunk_text(text: str, max_chars: int = 900) -> List[str]:
    """Chunk CV into ~max_chars segments without breaking too badly."""
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []

    for w in words:
        current.append(w)
        if len(" ".join(current)) >= max_chars:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# -------------------------------------------------------------------
# Embedding helpers
# -------------------------------------------------------------------


def _embed_text(text: str, task_type: str) -> Optional[np.ndarray]:
    """Embed a single piece of text; return vector or None on failure."""
    if not _try_configure_client():
        return None

    try:
        resp = genai.embed_content(
            model=EMBED_MODEL,
            content=text,
            task_type=task_type,
        )
        emb = resp.get("embedding") if isinstance(resp, dict) else getattr(resp, "embedding", None)
        if emb is None:
            return None
        return np.array(emb, dtype="float32")
    except Exception:
        return None


def _cosine_sim_matrix(query: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between query (D,) and docs (N, D)."""
    if docs.size == 0:
        return np.array([])
    qn = query / (np.linalg.norm(query) + 1e-8)
    dn = docs / (np.linalg.norm(docs, axis=1, keepdims=True) + 1e-8)
    return dn @ qn


# -------------------------------------------------------------------
# Core RAG implementation
# -------------------------------------------------------------------


class CVRAG:
    """RAG over Sergiu's CV with Gemini embeddings."""

    def __init__(self) -> None:
        # Load + chunk CV once
        cv_text = _load_cv_text()
        self.chunks: List[str] = _chunk_text(cv_text)
        self._embeddings: Optional[np.ndarray] = None  # lazy

    def _ensure_embeddings(self) -> bool:
        """Compute embeddings once on first query."""
        if self._embeddings is not None:
            return True

        if not self.chunks:
            self._embeddings = np.zeros((0, 1), dtype="float32")
            return True

        vecs: List[np.ndarray] = []
        for ch in self.chunks:
            v = _embed_text(ch, task_type="retrieval_document")
            if v is None:
                # If one chunk fails, fall back to zero vector for that chunk
                v = np.zeros(768, dtype="float32")
            vecs.append(v)

        self._embeddings = np.stack(vecs, axis=0)
        return True

    def _retrieve_top_k(self, question: str, k: int = 3) -> List[str]:
        if not self._ensure_embeddings():
            return []

        q_vec = _embed_text(question, task_type="retrieval_query")
        if q_vec is None:
            return []

        assert self._embeddings is not None
        sims = _cosine_sim_matrix(q_vec, self._embeddings)
        if sims.size == 0:
            return []

        # Indices of top-k similar chunks
        top_k_idx = np.argsort(sims)[-k:][::-1]
        return [self.chunks[int(i)] for i in top_k_idx]

    def query(self, question: str) -> str:
        """Return an answer grounded only in the CV."""
        # Try to retrieve relevant snippets
        relevant_chunks = self._retrieve_top_k(question, k=3)
        if not relevant_chunks:
            return "I couldn't find this information in Sergiu's CV."

        context = "\n\n---\n\n".join(relevant_chunks)

        if not _try_configure_client():
            # We still have relevant text, return it rather than failing
            return context

        # Tight, accuracy-focused prompt
        prompt = f"""
You are an assistant answering questions about a candidate based ONLY on their CV.

CV content:
{context}

Question:
{question}

Instructions:
- Answer concisely and directly.
- Use ONLY facts from the CV content above.
- If the CV does not contain the answer, say: "I couldn't find this information in Sergiu's CV."
- If the question is about phone, email, or location, output ONLY those fields in a simple sentence.
""".strip()

        try:
            model = genai.GenerativeModel(GEN_MODEL)
            resp = model.generate_content(prompt)
            text = getattr(resp, "text", None)
            if text:
                return text.strip()
            # Fallback to raw object if needed
            return str(resp)
        except Exception:
            # As a last resort, return the most relevant snippet
            return context


# -------------------------------------------------------------------
# Public accessor with safe fallback
# -------------------------------------------------------------------


def get_cv_rag():
    """Return a singleton CVRAG instance, or a safe dummy if init fails."""
    global _rag
    if _rag is None:
        try:
            _rag = CVRAG()
        except Exception:
            class Dummy:
                def query(self, q: str) -> str:
                    return "CV RAG unavailable. Ensure cv.txt and GOOGLE_API_KEY are correctly configured."
            _rag = Dummy()  # type: ignore[assignment]
    return _rag
