\# Sergiu – AI Recruiter Tour Agent (Google/Kaggle Agents Style)





This project implements an \*\*AI recruiter tour agent\*\* inspired by the Google / Kaggle agents course and whitepapers:





\- Introduction to Agents \& Architectures

\- Agent Quality

\- Context Engineering (Sessions \& Memory)

\- Agent Tools \& MCP

\- Prototype to Production





The agent:





\- Detects recruiters coming from \*\*GitHub / LinkedIn\*\*

\- Asks for the \*\*role\*\* and \*\*evaluation criteria\*\*

\- Uses \*\*embeddings\*\* to match the role + criteria to your most relevant projects

\- Can perform \*\*RAG over your CV\*\* to answer detailed questions

\- Generates an \*\*ATS-ready summary\*\* and \*\*recruiter follow-up email draft\*\*

\- Maintains a simple \*\*trajectory log\*\* (agent quality \& observability hook)





\## 1. Tech Stack





\- \*\*Backend\*\*: FastAPI + Uvicorn

\- \*\*Model\*\*: Gemini 1.5 Flash (via `google-genai`)

\- \*\*Embeddings\*\*: `text-embedding-004` for project and CV retrieval

\- \*\*Architecture\*\*: model + tools + orchestration (single-agent) with state and basic trajectory logging

\- \*\*Frontend\*\*: Static HTML + JS widget (GitHub Pages-ready)

\- \*\*Deployment\*\*: Google Cloud Run (buildpacks, no Docker required)





> Note: `google-adk` can be added later to wrap these tools into a formal ADK Agent, but this version focuses on the custom orchestrator as in the course.





---





\## 2. Project Structure





```text

recruiter-agent/

├── README.md

├── requirements.txt

├── main.py

├── app/

│ ├── \_\_init\_\_.py

│ ├── server.py

│ ├── agent.py

│ ├── tools.py

│ ├── cv\_rag.py

│ └── quality.py

└── frontend/

└── index.html

