# FastAPI REST API Development Guide

## Overview
FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.8+ based on standard Python type hints.

## Key Architecture Principles
1. **Pydantic Schemas**: Use Pydantic models for request body validation and response serialization.
2. **Dependency Injection**: Use `Depends` for common database sessions, authentication, and service instances.
3. **Async Support**: Use `async def` for I/O bound endpoints.
4. **Error Handling**: Raise `HTTPException` with explicit status codes (e.g. 400, 404, 500) and detailed messages.
5. **Testing**: Use `TestClient` from `starlette.testclient` or `httpx.AsyncClient` for automated testing.

## Example Pattern
```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Student Management API")

class Student(BaseModel):
    id: int
    name: str
    email: str

students_db = {}

@app.post("/students/", status_code=status.HTTP_201_CREATED)
def create_student(student: Student):
    if student.id in students_db:
        raise HTTPException(status_code=400, detail="Student ID already exists")
    students_db[student.id] = student
    return student
```
