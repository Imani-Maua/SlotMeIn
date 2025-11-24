from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import DatabaseError
from typing import Annotated
from sqlalchemy.orm import Session
from app.database.auth import User
from app.config.config import Settings
from app.authentication.tokens.schema import Payload
from app.authentication.tokens.service import TokenService
from app.authentication.utils.password_utils import verify_password

settings = Settings()
SECRET_KEY = settings.KEY
algorithm = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def lookup_user(db: Session, username: str| None = None, user_id: int| None = None):

    user = None
    if username is not None and user_id is not None:
        raise ValueError("Provide either username or user_id, not both")
    
    if username is not None:
        return db.query(User).filter(User.username == username).first()

    elif user_id is not None:
        return db.query(User).filter(User.id == user_id).first()

    return None

def authenticate_user(db: Session, username:str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")
    print(f"PASSWORD IS A MATCH:{verify_password(password=password, hash=user.pwd_hash)}")
    if not verify_password(password=password, hash=user.pwd_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    
    return user

def get_user_from_token(db: Session, token: Annotated[str, Depends(oauth2_scheme)]):
    token_data: Payload = TokenService.decode_token(token)
    user = lookup_user(db=db, user_id=token_data.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user

def user_is_active(user: Annotated[User, Depends(get_user_from_token)]):
    if user.is_active is not True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def activate_user_account(db: Session, user_id: int, hash: str):
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
