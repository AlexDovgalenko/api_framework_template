"""FastAPI application used by the dummy test-suite.

Key points
~~~~~~~~~~
• SQLite persistence via SQLAlchemy Core
• Authentication: JWT Bearer tokens AND HTTP Basic
• Uses the central logging configuration defined in logging_config.py
"""

import logging
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth_utils import authenticate_request, create_jwt_token
from app.db_utils import database_engine, metadata, users_table
from constants.common import APP_LOGGER_NAME, APP_TITLE

api_logger = logging.getLogger(APP_LOGGER_NAME)

### Create the database tables if, does not exist ###
metadata.create_all(database_engine)

### Create the FastAPI application instance ###
app = FastAPI(title=APP_TITLE)

### pydantic models ###
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str


class UserReadResponse(BaseModel):
    id: str
    email: EmailStr


### routes ###
@app.post("/users", status_code=201, response_model=UserReadResponse)
def create_user(user: UserCreateRequest):
    """Register a new user. 409 Conflict if email already exists."""
    user_id =  str(uuid4())
    insert_stmt = users_table.insert().values(
        id=user_id,
        email=user.email,
        pwd=user.password,
    )
    try:
        with database_engine.begin() as connection:
            connection.execute(insert_stmt)
    except IntegrityError:
        raise HTTPException(409, "User already exists")

    api_logger.info("Created user %s", user.email)
    return {"id": user_id, "email": user.email}


@app.get("/users/{email}", response_model=UserReadResponse)
def get_user_by_email(email: str):
    """Return user details or 404 if the email is unknown."""
    query = select(users_table.c.id, users_table.c.email).where(
        users_table.c.email == email
    )
    with database_engine.begin() as connection:
        row = connection.execute(query).fetchone()
    if not row:
        raise HTTPException(404, "Not Found")

    return {"id": row.id, "email": row.email}


@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Resource-owner-password flow:
    POST valid email+password → signed JWT token.
    """
    query = select(users_table).where(
        users_table.c.email == form_data.username,
        users_table.c.pwd == form_data.password,
    )
    with database_engine.begin() as connection:
        user_row = connection.execute(query).fetchone()

    if not user_row:
        raise HTTPException(401, "Incorrect username or password")

    return {
        "access_token": create_jwt_token(form_data.username),
        "token_type": "bearer",
    }


@app.get("/protected")
def protected_endpoint(authenticated_user: str = Depends(authenticate_request)):
    """Return a greeting – requires authentication."""
    return {"hello": authenticated_user}
