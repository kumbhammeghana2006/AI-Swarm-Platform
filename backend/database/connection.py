from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# Handle SQLite specific arguments if SQLite is used as fallback
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency that yields a database session and closes it after request completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
