# app/server.py — FastAPI wiring for recruiter-agent

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .agent import agent_turn
from .models import ChatRequest, ChatResponse, State


app = FastAPI()


# CORS so frontend (GitHub Pages, local dev, Cloud Run) can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Frontend serving (index.html from /frontend)
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/", include_in_schema=False)
async def serve_frontend_root():
    """
    Serve the main UI from frontend/index.html.
    This is what Cloud Run will show at the service root URL.
    """
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise RuntimeError(f"Frontend index.html not found at {index_path}")
    return FileResponse(index_path)


@app.get("/{path:path}", include_in_schema=False)
async def serve_frontend_assets(path: str):
    """
    Serve frontend static assets, or fall back to index.html for SPA routing.
    """
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    # Fallback for unknown routes (SPA-style routing)
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(index_path)


# ------------------------------------------------------------------
# /chat endpoint – main recruiter agent entrypoint
# ------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint used by the frontend.

    - We create a fresh State per request (stateless Cloud Run-friendly).
    - We pass (state, user_message) into agent_turn.
    - We wrap the result into a ChatResponse Pydantic model.
    """
    # Fresh state per request (you can later persist using session_id)
    state = State(source=req.source)

    # Run the agent graph
    result = agent_turn(state, req.message)

    # Ensure we don't return None (this caused the Cloud Run crash)
    if result is None:
        raise RuntimeError("agent_turn returned None")

    # Ensure required fields exist
    reply = result.get("reply")
    result_state = result.get("state")

    if reply is None:
        raise RuntimeError("agent_turn returned dict without 'reply'")

    # Build correct response model
    return ChatResponse(
        reply=reply,
        state=result_state,
        session_id=req.session_id,
    )
