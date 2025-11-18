"""Cloud-Run Safe CV RAG using Gemini embeddings."""

from __future__ import annotations

from typing import List, Tuple, Optional
import os

import numpy as np
import google.generativeai as genai

# Correct full GEMINI model paths
EMBED_MODEL = "models/text-embedding-004"
GEN_MODEL = "models/gemini-1.5-flash"


# ---- CLIENT (NO GLOBAL CACHING!) --------------------------------------------

def get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set on Cloud Run.")

    # Build fresh client each call: Cloud Run concurrency safe
    return genai.Client(api_key=api_key)


# ---- Embedding helpers -------------------------------------------------------

def _embed(text: str) -> List[float]:
    client = get_client()
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )

    emb = resp.embeddings[0]
    if hasattr(emb, "values"):
        return list(emb.values)
    if isinstance(emb, dict) and "values" in emb:
        return emb["values"]
    return list(emb)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ---- RAG Class ---------------------------------------------------------------

class CVRAG:
    def __init__(self) -> None:
        # FIX: works inside Cloud Run container
        base = os.path.dirname(__file__)
        cv_path = os.path.join(base, "cv.txt")

        if not os.path.exists(cv_path):
            raise FileNotFoundError(
                f"cv.txt not found at: {cv_path}. "
                "Ensure Dockerfile copies cv.txt into /app/app/"
            )

        with open(cv_path, "r", encoding="utf-8") as f:
            self.cv_text = f.read()

        self.chunks = self._chunk_text(self.cv_text)
        self.chunk_embeddings = [
            np.array(_embed(ch), dtype="float32")
            for ch in self.chunks
        ]

    def _chunk_text(self, text: str, max_chars: int = 900) -> List[str]:
        words = text.split()
        chunks = []
        current = []

        for w in words:
            current.append(w)
            if len(" ".join(current)) >= max_chars:
                chunks.append(" ".join(current))
                current = []

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _retrieve(self, question: str, top_k: int = 3):
        q_emb = np.array(_embed(question), dtype="float32")
        scored = []
        for ch, emb in zip(self.chunks, self.chunk_embeddings):
            score = _cosine(q_emb, emb)
            scored.append((score, ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:top_k]

    def query(self, question: str) -> str:
        try:
            client = get_client()
            chunks = self._retrieve(question)
            context = "\n\n---\n\n".join(ch for _, ch in chunks)

            prompt = f"""
You are an AI career assistant.

Relevant CV content:
{context}

User question:
{question}

Answer ONLY with info from the CV content above.
"""

            resp = client.models.generate_content(
                model=GEN_MODEL,
                contents=prompt,
            )
            return getattr(resp, "text", str(resp))

        except Exception as e:
            return f"CV RAG is temporarily unavailable. (internal error: {type(e).__name__})"


# ---- Singleton with fallback --------------------------------------------------

_rag: Optional[CVRAG] = None

def get_cv_rag():
    global _rag
    if _rag is None:
        try:
            _rag = CVRAG()
        except Exception:
            class Dummy:
                def query(self, q): 
                    return "CV RAG unavailable. Ensure cv.txt + API key are set."
            _rag = Dummy()
    return _rag
