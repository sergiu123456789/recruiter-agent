# app/server.py
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from .config import get_settings
from .telemetry import configure_logging, configure_tracer
from .routes import router as api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    # Initialize telemetry (your custom functions)
    configure_logging(settings)
    configure_tracer(settings)

    app = FastAPI(
        title="Recruiter Agent API",
        description="Match job descriptions to candidate profile",
        version="1.0.0",
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/")
    @app.get("/healthz")
    async def health():
        return {"status": "ok"}

    # Main API (frontend calls /api/v1/match)
    app.include_router(api_router, prefix="/api/v1", tags=["match"])

    # Instrumentations
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()   # LoggingInstrumentor removed

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    port = int(os.getenv("PORT", settings.port))  # now uses updated port

    uvicorn.run(
        "app.server:app",
        host=settings.host,
        port=port,
        reload=settings.environment == "local",
    )
