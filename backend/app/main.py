from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import audit, auth, users, complaints, evidence

from app.api import health

app = FastAPI(
    title="SafeWork API",
    description="Privacy-preserving workplace grievance documentation and triage. "
    "Supports, and never replaces, the Internal Committee.",
    version="0.1.0",
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(audit.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React/Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
# Phase 1 will add: app.include_router(auth.router, prefix="/auth")

app.include_router(complaints.router)
app.include_router(complaints.categories_router)
app.include_router(evidence.router)

from app.api import analysis  # noqa: E402
app.include_router(analysis.router)
