import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

load_dotenv()


def normalize_database_url(url: str) -> str:
    """
    Ensure PostgreSQL URLs explicitly use psycopg (psycopg 3).

    Neon commonly provides:
        postgresql://...

    SQLAlchemy 2.0 can otherwise try to load psycopg2.
    """
    if url.startswith("postgresql+psycopg://"):
        return url

    if url.startswith("postgresql://"):
        return url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    if url.startswith("postgres://"):
        return url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    return url


# Production-friendly option:
# use DATABASE_URL from Neon/managed PostgreSQL.
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

if DATABASE_URL_ENV:
    DATABASE_URL = normalize_database_url(
        DATABASE_URL_ENV
    )
else:
    DATABASE_URL = URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "research_agent"),
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)