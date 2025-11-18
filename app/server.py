# app/server.py

from typing import Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import agent_turn
from .cv_rag import get_cv_rag
from .models.state import State
from .quality import StepKind
from .session_store import load_session, save_session
from .judge import evaluate_agent_turn
from .utils.normalize import normalize_criteria

# -------------------------
# FastAPI + CORS
# -------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Request/Response Models
# -------------------------
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    source: Optional[str] = None
    role: Optional[str] = None
    criteria: Optional[list[str]] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class CVRequest(BaseModel):
    question: str


# --------- A2A (Agent-to-Agent) ---------
class A2ARecruiterRequest(BaseModel):
    role: str
    criteria: Optional[list[str]] = None
    job_description: Optional[str] = None


class A2ARecruiterResponse(BaseModel):
    recommended_projects: list[Dict[str, Any]]
    ats_summary: str
    email_template: str


# -------------------------
# Health check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Chat endpoint (main agent)
# -------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    # --- Load or create session ---
    session_id = req.session_id or "session-"
    state = load_session(session_id)
    if state is None:
        state = State()

    if req.source:
        state.source = req.source

    # -------- Trajectory: user step --------
    state.trajectory.add(
        kind=StepKind.user,
        message=req.message,
        meta={"source": state.source},
    )

    # -------- Agent turn --------
    out = agent_turn(state, req.message)
    new_state: State = out["state"]

    # -------- Trajectory: agent step --------
    new_state.trajectory.add(
        kind=StepKind.agent,
        message=out["reply"],
        meta={"role": new_state.role, "criteria": new_state.criteria},
    )

    # -------- LLM Judge Evaluation --------
    try:
        judge = evaluate_agent_turn(
            role=new_state.role,
            criteria=new_state.criteria,
            user_message=req.message,
            agent_reply=out["reply"],
        )

        new_state.trajectory.add(
            kind=StepKind.tool,
            message="llm_judge_evaluation",
            meta=judge,
        )

    except Exception as e:
        new_state.trajectory.add(
            kind=StepKind.tool,
            message="llm_judge_error",
            meta={"error": type(e).__name__},
        )

    # -------- Save session --------
    save_session(session_id, new_state)

    return ChatResponse(session_id=session_id, reply=out["reply"])


# -------------------------
# CV RAG Endpoint
# -------------------------
@app.post("/cv-rag")
def cv_rag_endpoint(req: CVRequest):
    rag = get_cv_rag()
    answer = rag.query(req.question)
    return {"answer": answer}


# -------------------------
# Admin API: Refresh GitHub Portfolio
# -------------------------
from .tools import force_refresh_portfolio

@app.post("/admin/refresh-portfolio")
def admin_refresh_portfolio():
    count = force_refresh_portfolio()
    return {"status": "ok", "projects_loaded": count}


# -------------------------
# A2A Recruiter Tool Endpoint
# -------------------------
from .tools import select_best_projects_for_role, generate_ats_summary_and_email

@app.post("/a2a/recruiter", response_model=A2ARecruiterResponse)
def a2a_recruiter(req: A2ARecruiterRequest):

    criteria = req.criteria or ["ml", "production"]

    projects = select_best_projects_for_role(req.role, criteria)
    summaries = generate_ats_summary_and_email(req.role, criteria, projects)

    return A2ARecruiterResponse(
        recommended_projects=projects,
        ats_summary=summaries["ats"],
        email_template=summaries["email"],
    )
