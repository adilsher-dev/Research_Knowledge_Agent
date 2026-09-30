import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import SessionLocal
from models import User

load_dotenv()

# --------------------------------------------------
# Config
# --------------------------------------------------
# JWT_SECRET must be set in the environment. We fail
# fast at import time rather than silently signing
# tokens with a missing/weak secret.

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 60 * 24 * 7  # 7 days

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is not set. Add it to backend/.env before starting the server."
    )

bearer_scheme = HTTPBearer(auto_error=False)


# --------------------------------------------------
# Passwords
# --------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# --------------------------------------------------
# JWT
# --------------------------------------------------

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Session expired. Please sign in again."
        )

    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials."
        )


# --------------------------------------------------
# FastAPI dependency
# --------------------------------------------------
# Every protected endpoint depends on this. It is the
# ONLY source of truth for "who is making this request" —
# routes must never accept a user_id from the request
# body or query params instead.

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    user_id = decode_access_token(credentials.credentials)

    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required."
            )

        db.expunge(user)
        return user

    finally:
        db.close()
