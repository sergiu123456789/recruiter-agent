🚀 Sergiu – AI Recruiter Tour Agent
Production-ready AI Agent (Google/Kaggle Agents Style)

This project implements a production-grade AI Recruiter Tour Agent inspired by the Google/Kaggle “Agents” course and recent agent architecture best practices.

It acts as an interactive recruiter companion, helping hiring managers instantly understand your strongest qualifications through:

Smart role detection

Criteria-based project selection

CV-RAG Q&A

ATS-ready summaries

Recruiter email drafting

Session memory + trajectory logging

Auto-start when arriving from GitHub or LinkedIn

Designed as a single-agent with tools, following modern agentic patterns:

Model (LLM) →

Tools (RAG, portfolio, ATS) →

Orchestrator →

State + Trajectory →

Frontend widget

🧠 Core Capabilities
✔️ Recruiter-Aware Entry

Detects if the visitor came from GitHub or LinkedIn, then tailors the first message.

✔️ Role & Criteria Extraction

Understands roles like:

Senior ML Engineer

AI Engineer

NLP Researcher

Data Scientist

And recruiter criteria such as:

Production RAG

Ownership

Leadership

Communication

✔️ Project Relevance Ranking

Uses embeddings to compute a shortlist of the most relevant projects based on:

Role

Criteria

Tags

Summary text

Impact statements

✔️ Deep-Dive Flow

Walks recruiters project-by-project, explaining:

What the project does

Impact

Why it matches the role + criteria

✔️ ATS-Ready Summary + Recruiter Email Draft

Creates:

A polished ATS paragraph

A recruiter follow-up email template

✔️ CV RAG (Gemini Embeddings)

Chunked CV retrieval using text-embedding-004, then answer generation using Gemini 1.5 Flash.

✔️ Agent Quality & Observability

Lightweight trajectory logging:

user step

agent step

tool step

LLM judge evaluation (1–5 score)

🏗️ Tech Stack

Backend: FastAPI, Uvicorn

LLM: Gemini 1.5 Flash (google-genai)

Embeddings: models/text-embedding-004

Architecture: Custom single-agent orchestrator with tools

Frontend: Small JS widget (GitHub Pages compatible)

Deployment: Google Cloud Run

Storage: In-memory session store (extendable)

Buildpacks deployment works, but Dockerfile is included for full control.

📁 Project Structure
recruiter-agent/
├── README.md
├── requirements.txt
├── main.py
├── app/
│   ├── __init__.py
│   ├── server.py
│   ├── agent.py
│   ├── tools.py
│   ├── cv_rag.py
│   ├── quality.py
│   ├── models/
│   │   └── state.py
│   └── session_store.py
└── frontend/
    └── index.html

🚀 Deployment (Cloud Run)

Ensure GOOGLE_API_KEY is available (Cloud Run → Variables).

Deploy with Docker:

gcloud run deploy recruiter-agent \
    --source . \
    --platform managed \
    --allow-unauthenticated \
    --region europe-west1 \
    --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY


Or with your included PowerShell script (deploy.ps1).

