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
    task_type: Optional[str] = None
) -> Task:
    """
    Creates a Task record in DB, executes existing LangGraph swarm,
    stores TaskResult, updates task status, and returns Task.
    """
    if not task_text or not task_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task text cannot be empty."
        )

    # 1. Create DB Task record with status RUNNING
    task = crud.create_task(db=db, user_id=user.id, task_text=task_text, task_type=task_type)
    
    # 2. Execute existing Phase 1 LangGraph swarm workflow
    swarm_result = execute_swarm_task(task_text=task_text, override_type=task_type)
    
    # 3. Store execution result and update status
    exec_status = "SUCCESS" if swarm_result["success"] else "FAILED"
    task_status = "COMPLETED" if swarm_result["success"] else "FAILED"
    
    crud.create_task_result(
        db=db,
        task_id=task.id,
        final_output=swarm_result["final_output"],
        execution_status=exec_status,
        iteration_count=swarm_result["iteration_count"]
    )
    
    updated_task = crud.update_task_status(db=db, task_id=task.id, status=task_status)
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
