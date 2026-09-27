from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import crud
from backend.database.models import User
from backend.auth.schemas import TaskCreate, TaskResponse
from backend.api.dependencies import get_current_user, require_admin
from backend.services import task_service

health_router = APIRouter(tags=["Health"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@health_router.get("/health")
def health_check():
    """Simple health check endpoint returning API status."""
    return {"status": "ok", "service": "AI-Swarm-Platform Backend"}

@tasks_router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_input: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a Task, triggers existing Phase 1 LangGraph swarm execution,
    persists TaskResult, and returns response to authenticated user.
    """
    task = task_service.create_and_execute_task(
        db=db,
        user=current_user,
        task_text=task_input.task_text,
        task_type=task_input.task_type
    )
    return task

@tasks_router.get("", response_model=List[TaskResponse])
def list_user_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns task and result history for the authenticated user only."""
    return task_service.get_user_tasks(db=db, user_id=current_user.id)

@tasks_router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns details for a specific task owned by user or accessible to ADMIN."""
    return task_service.get_user_task_by_id(db=db, task_id=task_id, user=current_user)

@admin_router.get("/tasks", response_model=List[TaskResponse])
def list_all_system_tasks(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint: returns task history for all users across the system."""
    return crud.get_all_tasks(db)
