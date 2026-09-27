import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure root directory is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import settings
from backend.database.connection import init_db
from backend.auth.routes import router as auth_router
from backend.api.routes import health_router, tasks_router, admin_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Backend Layer for AI Swarm Platform with JWT Auth, PostgreSQL/SQLite Persistence, and LangGraph Integration"
)

# CORS middleware for future frontend (Phase 3) communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-initialize database tables on application startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
