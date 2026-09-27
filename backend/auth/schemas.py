from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

# --- User Schemas ---

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "USER"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None

# --- Task & Result Schemas ---

class TaskCreate(BaseModel):
    task_text: str
    task_type: Optional[str] = None

class TaskResultResponse(BaseModel):
    id: int
    task_id: int
    final_output: Optional[str] = None
    execution_status: str
    iteration_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    user_id: int
    task_text: str
    task_type: Optional[str] = None
    status: str
    created_at: datetime
    result: Optional[TaskResultResponse] = None

    class Config:
        from_attributes = True
