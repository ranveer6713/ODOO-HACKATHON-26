<<<<<<< HEAD
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import JWTError, jwt
import bcrypt

# JWT configurations
SECRET_KEY = "assetflow-hackathon-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def hash_password(password: str) -> str:
    return get_password_hash(password)


def create_access_token(
    data: Optional[dict] = None,
    subject: Optional[Union[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = {}
    if data is not None:
        to_encode = data.copy()
    elif subject is not None:
        to_encode = {"sub": str(subject)}

    if "exp" not in to_encode:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

#azdf
=======
"""Authentication seam for the AssetFlow foundation.

Every module consumes :class:`Principal` and :func:`get_current_user` from here.
The production system decodes a bearer JWT; for this deployment the identity is
carried on lightweight forwarded headers minted by the frontend at sign-in:

    X-User-Id     -- string principal id (string-FK contract, e.g. ``EMP-1001``)
    X-User-Role   -- one of :class:`app.core.enums.Role`
    Authorization -- ``Bearer demo.<id>.<role>`` (fallback source for the above)

Identity is resolved from those headers; nothing is invented. A request that
carries no identity is rejected with ``401`` rather than being silently granted a
principal — matching how the real JWT seam behaves.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status
from pydantic import BaseModel

from app.core.enums import Role


class Principal(BaseModel):
    """The authenticated caller, derived from the request's identity headers.

    User identifiers are strings to honour the string-FK integration contract
    shared across the AssetFlow modules.
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


def _role_from_str(raw: Optional[str]) -> Optional[Role]:
    if not raw:
        return None
    try:
        return Role(raw.strip().lower())
    except ValueError:
        return None


def _from_bearer(token: str) -> tuple[Optional[str], Optional[Role]]:
    """Parse the demo bearer token ``demo.<id>.<role>`` into (id, role)."""
    if not token.lower().startswith("bearer "):
        return None, None
    value = token[7:].strip()
    parts = value.split(".")
    if len(parts) >= 3 and parts[0] == "demo":
        # role is the final segment; id is everything between (ids contain no dots)
        return parts[1], _role_from_str(parts[-1])
    return None, None


def get_current_user(request: Request) -> Principal:
    """Resolve the authenticated principal from the request's identity headers."""
    user_id = request.headers.get("X-User-Id")
    role = _role_from_str(request.headers.get("X-User-Role"))

    if not user_id or role is None:
        # Fall back to the bearer token so a client that only sets Authorization
        # still authenticates.
        auth = request.headers.get("Authorization", "")
        bearer_id, bearer_role = _from_bearer(auth)
        user_id = user_id or bearer_id
        role = role or bearer_role

    if not user_id or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Principal(
        id=user_id,
        role=role,
        email=request.headers.get("X-User-Email"),
        name=request.headers.get("X-User-Name"),
    )
>>>>>>> 7cb671b ( final updates)
