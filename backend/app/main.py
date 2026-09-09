from app.routes.audit_log import (
    router as audit_log_router,
)

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.routes.projects import (
    router as projects_router,
)

from app.routes.activities import (
    router as activities_router,
)

from app.routes.field_events import (
    router as field_events_router,
)

from app.routes.auth import (
    router as auth_router,
)

from app.routes.extraction import (
    router as extraction_router,
)

from app.routes.matches import (
    router as matches_router,
)

from app.routes.field_twin import (
    router as field_twin_router,
)

from app.routes.ingestion import (
    router as ingestion_router,
)

from app.routes.project_knowledge import (
    router as project_knowledge_router,
)

from app.routes.exceptions import (
    router as exceptions_router,
)

from app.routes.schedule_import import (
    router as schedule_import_router,
)


app = FastAPI(
    title="Field Progress API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    projects_router
)

app.include_router(
    activities_router
)

app.include_router(
    field_events_router
)

app.include_router(
    auth_router
)

app.include_router(
    extraction_router
)

app.include_router(
    matches_router
)

app.include_router(
    field_twin_router
)

app.include_router(
    ingestion_router
)

app.include_router(
    project_knowledge_router
)

app.include_router(
    exceptions_router
)

app.include_router(
    schedule_import_router
)

app.include_router(
    audit_log_router
)


@app.get("/")
def root():

    return {
        "message":
            "Field Progress API is running"
    }


@app.get("/health")
def health():

    return {
        "status":
            "healthy"
    }