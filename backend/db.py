import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/bgg_analysis_dev")

# Engine and session factory
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_db_session():
    """Yield a SQLAlchemy Session. Commits on success, rolls back on exception, always closes."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create DB tables from models. Call once during local setup or in a migration-less scenario."""
    # import models here to avoid circular imports at module import time
    from . import models

    models.Base.metadata.create_all(bind=engine)

    print("\nDatabase initialized successfully.\n")
