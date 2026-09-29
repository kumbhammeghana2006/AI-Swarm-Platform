from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

SUPPORTED_CONFIGURATION_TYPES = {"multi_agent"}
FUTURE_CONFIGURATION_TYPES = {"single_agent"}

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
    configuration_type: Optional[str] = "multi_agent"

    @field_validator("configuration_type")
    @classmethod
    def validate_configuration_type(cls, v: Optional[str]) -> str:
        if v is None:
            return "multi_agent"
        clean = v.strip().lower()
        if clean == "single_agent":
            raise ValueError(
                "Configuration type 'single_agent' is not currently supported for execution. "
                "Only 'multi_agent' swarm execution is active in this milestone."
            )
        if clean not in SUPPORTED_CONFIGURATION_TYPES:
            raise ValueError(
                f"Invalid configuration_type '{v}'. Supported configuration is 'multi_agent'."
            )
        return clean

class TaskResultResponse(BaseModel):
    id: int
    task_id: int
    final_output: Optional[str] = None

    # Evaluation Metrics
    execution_status: str
    iteration_count: int
    execution_time_seconds: Optional[float] = None
    tester_result: Optional[str] = None
    agents_used: Optional[List[str]] = None
    configuration_type: str = "multi_agent"

    # Metadata
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
