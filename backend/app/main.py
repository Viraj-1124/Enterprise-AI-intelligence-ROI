from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database.session import Base, engine
from app.models import models  # noqa: F401 ensure models are registered
from app.api import auth, organization, tasks, sessions, ai_usage, outcomes, roi, dashboard, prompts, connectors

app = FastAPI(title="Enterprise AI Intelligence & ROI Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(tasks.router)
app.include_router(sessions.router)
app.include_router(ai_usage.router)
app.include_router(outcomes.router)
app.include_router(roi.router)
app.include_router(dashboard.router)
app.include_router(prompts.router)
app.include_router(connectors.router)
