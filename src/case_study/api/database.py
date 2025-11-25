"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Database connection string
# Support DATABASE_URL or construct from individual env vars with local defaults
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Construct from individual environment variables with local defaults
    db_user = os.getenv("POSTGRES_USER", "fintela")
    db_password = os.getenv("POSTGRES_PASSWORD", "fintela_password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "fintela")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

