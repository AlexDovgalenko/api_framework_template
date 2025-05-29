import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, OAuth2PasswordBearer, HTTPBasic
from sqlalchemy import select

from app.db_utils import users_table, database_engine
from utils.constants import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_TTL_MIN

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)
basic_scheme  = HTTPBasic(auto_error=False)

def create_jwt_token(user_email: str) -> str:
    """Return a signed JWT containing the user email and an expiry timestamp."""
    payload = {
        "sub": user_email,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_TTL_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> str:
    """Validate the token and return the user email."""
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return data["sub"]
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid or expired token") from exc


def authenticate_request(
    bearer_token: str | None = Depends(oauth2_scheme),
    basic_credentials: HTTPBasicCredentials | None = Depends(basic_scheme),
) -> str:
    """Authenticate the incoming request using either Bearer or Basic credentials.

    Returns
    -------
    str – the authenticated user email.
    """
    if bearer_token:
        return verify_jwt_token(bearer_token)

    if basic_credentials:
        query = (
            select(users_table.c.pwd)
            .where(users_table.c.email == basic_credentials.username)
        )
        with database_engine.begin() as connection:
            row = connection.execute(query).fetchone()

        if row and secrets.compare_digest(row.pwd, basic_credentials.password):
            return basic_credentials.username

    raise HTTPException(
        401,
        "Unauthenticated",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )

