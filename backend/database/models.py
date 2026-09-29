from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="USER", nullable=False)  # "USER" or "ADMIN"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_text = Column(Text, nullable=False)
    task_type = Column(String, nullable=True)
    status = Column(String, default="PENDING", nullable=False) # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="tasks")
    result = relationship("TaskResult", back_populates="task", uselist=False, cascade="all, delete-orphan")

class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, unique=True, index=True)
    final_output = Column(Text, nullable=True)

    # Evaluation Metrics
    execution_status = Column(String, nullable=False)  # "SUCCESS" or "FAILED"
    iteration_count = Column(Integer, default=1, nullable=False)
    execution_time_seconds = Column(Float, nullable=True)
    tester_result = Column(String, nullable=True)  # "PASS", "FAIL", "N/A"
    agents_used = Column(JSON, nullable=True)  # E.g. ["Classifier", "Planner", "Coder", ...]
    configuration_type = Column(String, default="multi_agent", nullable=False)  # "multi_agent" or "single_agent"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="result")
