from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import User, Task, TaskResult

# --- User CRUD ---

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, hashed_password: str, role: str = "USER") -> User:
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role.upper()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Task & TaskResult CRUD ---

def create_task(db: Session, user_id: int, task_text: str, task_type: Optional[str] = None) -> Task:
    db_task = Task(
        user_id=user_id,
        task_text=task_text,
        task_type=task_type,
        status="RUNNING"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task_status(db: Session, task_id: int, status: str) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = status
        db.commit()
        db.refresh(task)
    return task

def create_task_result(
    db: Session,
    task_id: int,
    final_output: str,
    execution_status: str,
    iteration_count: int
) -> TaskResult:
    result = TaskResult(
        task_id=task_id,
        final_output=final_output,
        execution_status=execution_status,
        iteration_count=iteration_count
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def get_tasks_by_user(db: Session, user_id: int) -> List[Task]:
    return db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).all()

def get_task_by_id_and_user(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()

def get_all_tasks(db: Session) -> List[Task]:
    return db.query(Task).order_by(Task.created_at.desc()).all()
