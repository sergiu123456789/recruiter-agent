# app/judge.py
from __future__ import annotations

from typing import Dict, Any, List, Optional
import os
import json

# FIX: correct Google Generative AI import
import google.generativeai as genai

GEN_MODEL = "models/gemini-1.5-flash"

_client: Optional[genai.GenerativeModel] = None


def get_client() -> genai.GenerativeModel:
    global _client

    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")

        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel(GEN_MODEL)

    return _client


def evaluate_agent_turn(
    role: Optional[str],
    criteria: Optional[List[str]],
    user_message: str,
    agent_reply: str,
) -> Dict[str, Any]:

    model = get_client()

    crit_text = ", ".join(criteria or [])
    prompt = f"""
You are an expert technical recruiter evaluating an AI assistant's response.

Job role: {role or "unknown"}
Evaluation criteria: {crit_text or "not specified"}

User message:
{user_message}

Agent reply:
{agent_reply}

Evaluate the reply on this 1–5 scale:
- 5: Excellent and highly relevant
- 4: Good, minor issues
- 3: Mixed (some strengths, some weaknesses)
- 2: Weak
- 1: Off-topic, misleading, or problematic

Respond ONLY as JSON with this schema:
{{
  "score": <number 1-5>,
  "issues": ["short issue labels"],
  "notes": "one or two sentences explaining your rating"
}}
"""

    resp = model.generate_content(prompt)
    text = getattr(resp, "text", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "score": 3,
            "issues": ["judge_parse_error"],
            "notes": text[:200],
        }
