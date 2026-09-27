from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import crud
from backend.auth.schemas import UserRegister, UserLogin, UserResponse, Token
from backend.auth import security

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user after verifying username and email uniqueness."""
    # Check duplicate username
    if crud.get_user_by_username(db, username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered."
        )
    # Check duplicate email
    if crud.get_user_by_email(db, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
    
    # Hash password with scrypt
    hashed_pwd = security.hash_password(user_data.password)
    
    # Create user record
    role = user_data.role if user_data.role and user_data.role.upper() in ("USER", "ADMIN") else "USER"
    new_user = crud.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        role=role
    )
    return new_user

@router.post("/login", response_model=Token)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a signed JWT access token."""
    user = crud.get_user_by_username(db, username=login_data.username)
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token with identity & authorization role
    access_token = security.create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )
    return Token(access_token=access_token, token_type="bearer")
