"""Integration seam between the Workflow module and the shared foundation.

The Workflow module does NOT own the declarative Base, the DB session, or the
authenticated-user dependency. Person 1 provides those under ``app.database`` and
``app.core.security``. We import them when present and fall back to a local,
self-contained setup otherwise, so this package stays importable and testable in
isolation with zero hard coupling to un-owned files at import time.
"""
from typing import Optional

# --- Declarative Base -------------------------------------------------------
try:  # shared foundation (owned by Person 1)
    from app.database import Base  # type: ignore
except Exception:  # pragma: no cover - standalone / test fallback
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

# --- DB session dependency --------------------------------------------------
try:
    from app.database import get_db  # type: ignore
except Exception:  # pragma: no cover
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    _engine = create_engine(
        "sqlite:///./workflow_dev.db",
        connect_args={"check_same_thread": False},
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    def get_db():
        db = _SessionLocal()
        try:
            yield db
        finally:
            db.close()


# --- Current user (identity comes purely from JWT claims) -------------------
try:
    from app.core.security import get_current_user  # type: ignore
except Exception:  # pragma: no cover

    class CurrentUser:
        """Stand-in mirroring the JWT claim contract (sub, role, department_id)."""

        def __init__(self, id: str, role: str, department_id: Optional[str] = None):
            self.id = id
            self.role = role
            self.department_id = department_id

    def get_current_user() -> "CurrentUser":
        # Real implementation lives in the shared foundation; tests override this
        # via ``app.dependency_overrides``.
        raise RuntimeError(
            "get_current_user is provided by app.core.security (shared foundation)."
        )
