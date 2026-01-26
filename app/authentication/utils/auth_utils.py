"""
Authentication utility functions for user management and JWT token handling.

This module provides core authentication functionality including user lookup,
password verification, token-based authentication, and user account activation.
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import DatabaseError
from typing import Annotated
from sqlalchemy.orm import Session
from app.database.auth import User
from app.database.session import session
from app.config.config import Settings
from app.authentication.tokens.schema import Payload
from app.authentication.tokens.service import TokenService
from app.authentication.utils.password_utils import verify_password

settings = Settings()
SECRET_KEY = settings.KEY
algorithm = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def lookup_user(db: Session, username: str | None = None, user_id: int | None = None) -> User | None:
    """
    Look up a user in the database by username or user ID.

    Args:
        db: Database session for querying users.
        username: Optional username to search for.
        user_id: Optional user ID to search for.

    Returns:
        User object if found, None otherwise.

    Raises:
        ValueError: If both username and user_id are provided.
    """
    if username is not None and user_id is not None:
        raise ValueError("Provide either username or user_id, not both")
    
    if username is not None:
        return db.query(User).filter(User.username == username).first()

    elif user_id is not None:
        return db.query(User).filter(User.id == user_id).first()

    return None


def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    Authenticate a user with username and password.

    Args:
        db: Database session for querying users.
        username: Username of the user attempting to authenticate.
        password: Plain text password to verify.

    Returns:
        User object if authentication is successful.

    Raises:
        HTTPException: 404 if user doesn't exist, 401 if password is incorrect.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )
    
    if not verify_password(password=password, hash=user.pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def get_user_from_token(db: Session, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Extract and validate user from JWT token.

    Args:
        db: Database session for querying users.
        token: JWT token from the Authorization header.

    Returns:
        User object associated with the token.

    Raises:
        HTTPException: 404 if user not found, 401 if token is invalid.
    """
    token_data: Payload = TokenService.decode_token(token)
    user = lookup_user(db=db, user_id=token_data.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def user_is_active(user: Annotated[User, Depends(get_user_from_token)]) -> User:
    """
    Verify that the authenticated user account is active.

    Args:
        user: User object from token validation.

    Returns:
        User object if account is active.

    Raises:
        HTTPException: 403 if user account is inactive.
    """
    if user.is_active is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user


def get_current_user(
    db: Annotated[Session, Depends(session)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Get the current authenticated and active user from JWT token.
    
    This is the main dependency to use for protecting routes that require authentication.

    Args:
        db: Database session for querying users.
        token: JWT token from the Authorization header.

    Returns:
        Active User object associated with the token.

    Raises:
        HTTPException: 401 if token is invalid, 404 if user not found, 403 if user is inactive.
    """
    user = get_user_from_token(db=db, token=token)
    return user_is_active(user=user)


def activate_user_account(db: Session, user_id: int, hash: str) -> User:
    """
    Activate a user account and set their password hash.

    This is typically called when a user accepts an invitation and sets their password.

    Args:
        db: Database session for updating the user.
        user_id: ID of the user to activate.
        hash: Hashed password to set for the user.

    Returns:
        Updated User object with active status.

    Raises:
        HTTPException: 404 if user not found.
        DatabaseError: If database operation fails.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        user.pwd_hash = hash
        user.is_active = True
        db.commit()
        db.refresh(user)  
        return user

    except DatabaseError:
        db.rollback()
        raise DatabaseError(
            "A database error has occurred during account activation. Please try again"
        )
