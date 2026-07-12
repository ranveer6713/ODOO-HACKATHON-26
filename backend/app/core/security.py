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