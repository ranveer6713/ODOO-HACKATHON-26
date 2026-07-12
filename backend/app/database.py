<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/assetflow"
)

# Convert relative SQLite path to absolute path relative to backend root
if DATABASE_URL.startswith("sqlite:///./"):
    db_name = DATABASE_URL.replace("sqlite:///./", "")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, db_name)}"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
=======
"""Shared database foundation for the AssetFlow backend.

This is the single seam that every self-contained module consumes through its
local ``deps.py`` (``from app.database import Base, get_db``). Providing it here
unifies every module onto **one** declarative ``Base`` / metadata and **one**
SQLite (or Postgres) session, so cross-module readers (Dashboard, Reports) and
the string-FK ``assets`` contract all resolve against the same database.

Modules were written to fall back to isolated per-module SQLite files when this
module is absent; once it exists they all bind here instead — no module code
changes required.
"""
from __future__ import annotations

import os
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Engine / session
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assetflow.db")

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True
)

# The one declarative base shared by every module's ORM models.
Base = declarative_base()


def get_db() -> Iterator[Session]:
    """Yield a request-scoped session that is always closed.

    This is the production ``get_db`` that every module's ``deps.py`` imports.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
>>>>>>> 7cb671b ( final updates)
