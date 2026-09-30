from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import crud
from backend.database.models import User
from backend.auth.schemas import (
    TaskCreate,
    TaskResponse,
    MetricsSummaryResponse,
    ExperimentConfigResponse
)
from backend.api.dependencies import get_current_user, require_admin
from backend.services import task_service
from backend.services.metrics_service import calculate_metrics_summary
from backend.experiments.ablation import get_registered_experiments

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
        task_type=task_input.task_type,
        configuration_type=task_input.configuration_type or "multi_agent"
    )
    return task

@tasks_router.get("", response_model=List[TaskResponse])
def list_user_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns task and result history for the authenticated user only."""
    return task_service.get_user_tasks(db=db, user_id=current_user.id)

@tasks_router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def get_task_metrics_summary(
    scope: Optional[str] = Query(None, description="Scope of metrics: 'user' or 'global' (global requires ADMIN)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns empirical evaluation metrics summary.
    Normal users receive metrics for their own tasks only.
    ADMIN users receive global system-wide metrics by default or user-scoped metrics if requested.
    """
    if current_user.role == "ADMIN" and scope != "user":
        tasks = crud.get_all_tasks(db)
        return calculate_metrics_summary(tasks, scope="global")
    else:
        tasks = crud.get_tasks_by_user(db=db, user_id=current_user.id)
        return calculate_metrics_summary(tasks, scope="user")

@tasks_router.get("/experiments/configurations", response_model=List[ExperimentConfigResponse])
def list_experiment_configurations(
    current_user: User = Depends(get_current_user)
):
    """
    Returns registered experiment and ablation configurations for benchmark comparison.
    """
    return get_registered_experiments()

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

@admin_router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def get_admin_global_metrics_summary(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint: returns system-wide evaluation metrics summary across all users."""
    tasks = crud.get_all_tasks(db)
    return calculate_metrics_summary(tasks, scope="global")

