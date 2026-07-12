"""Integration seam between the Booking module and the shared foundation.

The Booking module is a self-contained vertical slice. It does **not** own the
declarative ``Base``, the database session, JWT/auth, or the ``users`` /
``assets`` tables — those belong to the shared foundation (Person 1). We consume
them when present and fall back to a local, standalone setup otherwise, so this
package stays importable, runnable and unit-testable in complete isolation with
zero hard coupling to files we do not own.
"""
from __future__ import annotations

import enum
from typing import Callable, Iterator, Optional

from fastapi import Depends

from app.booking.exceptions import AuthenticationError, PermissionDeniedError

# ---------------------------------------------------------------------------
# Declarative Base (owned by the shared foundation, consumed here)
# ---------------------------------------------------------------------------
try:  # pragma: no cover - exercised implicitly by whichever branch is live
    from app.database import Base  # type: ignore
except Exception:  # foundation not yet wired: stand up an isolated Base
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------
try:  # pragma: no cover
    from app.database import get_db  # type: ignore
except Exception:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    _engine = create_engine(
        "sqlite:///./booking.db",
        connect_args={"check_same_thread": False},
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=_engine, autocommit=False, autoflush=False, future=True
    )

    def get_db() -> Iterator["Session"]:
        """Yield a scoped session that is always closed."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Authentication / identity (identity comes purely from JWT claims upstream)
# ---------------------------------------------------------------------------
try:  # pragma: no cover
    from app.core.enums import Role  # type: ignore
    from app.core.security import Principal, get_current_user  # type: ignore
except Exception:
    from pydantic import BaseModel

    class Role(str, enum.Enum):
        """RBAC roles, sourced from the JWT ``role`` claim by the foundation."""

        EMPLOYEE = "employee"
        DEPARTMENT_HEAD = "department_head"
        TECHNICIAN = "technician"
        ASSET_MANAGER = "asset_manager"
        ADMIN = "admin"

    class Principal(BaseModel):
        """The authenticated caller, derived from JWT claims.

        User identifiers are strings to honour the string-FK integration
        contract shared across the AssetFlow modules.
        """

        id: str
        role: Role
        department_id: Optional[str] = None
        email: Optional[str] = None
        name: Optional[str] = None

        @property
        def is_admin(self) -> bool:
            return self.role == Role.ADMIN

        def has_role(self, *roles: "Role") -> bool:
            return self.is_admin or self.role in roles

    def get_current_user() -> "Principal":
        """Resolve the authenticated principal.

        The real implementation lives in the shared foundation
        (``app.core.security``) and decodes the bearer JWT. When the foundation
        is not present this seam refuses rather than inventing an identity;
        tests substitute a principal via ``app.dependency_overrides``.
        """
        raise AuthenticationError(
            "Authentication is provided by the shared foundation "
            "(app.core.security.get_current_user)."
        )


# ---------------------------------------------------------------------------
# Role-gate dependency factory
# ---------------------------------------------------------------------------
def require_roles(*allowed: "Role") -> Callable[..., "Principal"]:
    """Build a FastAPI dependency admitting only the given roles (admin always)."""

    def dependency(current: "Principal" = Depends(get_current_user)) -> "Principal":
        if current.is_admin or current.role in allowed:
            return current
        raise PermissionDeniedError(
            "You do not have permission to perform this action"
        )

    return dependency
