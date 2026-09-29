from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.database import crud
from backend.database.models import Task, User
from backend.services.swarm_service import execute_swarm_task

def create_and_execute_task(
    db: Session,
    user: User,
    task_text: str,
    task_type: Optional[str] = None,
    configuration_type: str = "multi_agent"
) -> Task:
    """
    Creates a Task record in DB, executes existing LangGraph swarm,
    stores TaskResult with evaluation metrics, updates task status, and returns Task.
    """
    if not task_text or not task_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task text cannot be empty."
        )

    # Validate execution configuration
    config_type = (configuration_type or "multi_agent").strip().lower()
    if config_type == "single_agent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Configuration type 'single_agent' is not currently supported for execution. "
                "Only 'multi_agent' swarm execution is active in this milestone."
            )
        )
    if config_type != "multi_agent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported configuration_type '{configuration_type}'. Only 'multi_agent' is supported."
        )

    # 1. Create DB Task record with status RUNNING
    task = crud.create_task(db=db, user_id=user.id, task_text=task_text, task_type=task_type)
    
    # 2. Execute existing Phase 1 LangGraph swarm workflow and capture evaluation metrics
    swarm_result = execute_swarm_task(
        task_text=task_text,
        override_type=task_type,
        configuration_type=configuration_type
    )
    
    # 3. Store execution result with evaluation metrics and update status
    exec_status = "SUCCESS" if swarm_result["success"] else "FAILED"
    task_status = "COMPLETED" if swarm_result["success"] else "FAILED"
    resolved_task_type = swarm_result.get("task_type") or task_type
    
    crud.create_task_result(
        db=db,
        task_id=task.id,
        final_output=swarm_result["final_output"],
        execution_status=exec_status,
        iteration_count=swarm_result["iteration_count"],
        execution_time_seconds=swarm_result.get("execution_time_seconds"),
        tester_result=swarm_result.get("tester_result"),
        agents_used=swarm_result.get("agents_used"),
        configuration_type=swarm_result.get("configuration_type", configuration_type)
    )
    
    updated_task = crud.update_task_status(
        db=db,
        task_id=task.id,
        status=task_status,
        task_type=resolved_task_type
    )
    return updated_task

def get_user_tasks(db: Session, user_id: int) -> List[Task]:
    """Returns task history for the specified user."""
    return crud.get_tasks_by_user(db=db, user_id=user_id)

def get_user_task_by_id(db: Session, task_id: int, user: User) -> Task:
    """Returns a specific task if user owns it or if user is ADMIN."""
    if user.role == "ADMIN":
        task = db.query(Task).filter(Task.id == task_id).first()
    else:
        task = crud.get_task_by_id_and_user(db=db, task_id=task_id, user_id=user.id)
        
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied."
        )
    return task
