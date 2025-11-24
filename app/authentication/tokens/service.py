from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import update, insert
from sqlalchemy.exc import DatabaseError
from datetime import datetime, timedelta
from jose import jwt,JWTError, ExpiredSignatureError
import uuid
from app.config.config import Settings
from app.auth.utils.utils import hash_password
from app.auth.token.auth_schema import Payload, Token
from app.database.auth import InviteToken, AccessToken, User
from app.auth.utils.utils import verify_password
from app.core.utils.enums import TokenType



settings = Settings()
SECRET_KEY = settings.KEY
algorithm = "HS256"



def create_token(data:Payload, expiry: timedelta):
        
        now = datetime.now() 
        expire = now + expiry
        data.exp = expire
        data.iat = now
        data.jti = str(uuid.uuid4())
        token = jwt.encode(data.model_dump(), SECRET_KEY, algorithm=algorithm)
        return token
    
def hash_token(token: str):
    return hash_password(token)

def store_token(db: Session, data: Payload, jwt: str):
    token = hash_token(jwt)
    if data.type == TokenType.invite.value:
        stmt = (insert(InviteToken).values(token_hash=token, user_id=data.id, jti=data.jti, expires_at=data.exp, created_at=data.iat).returning(InviteToken))
        result = db.execute(stmt)
        db.commit()
        invite_token = result.scalar_one()
        return invite_token
    
    if data.type == TokenType.access.value:
        stmt = (insert(AccessToken).values(token_hash=token, user_id=data.id, jti=data.jti, expires_at=data.exp, created_at=data.iat).returning(AccessToken))
        result = db.execute(stmt)
        db.commit()
        access_token = result.scalar_one()
        return access_token

def decode_token(token: str) -> Payload:

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                  detail="Invalid token")
        return payload
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                  detail="Invalid token")

def verify_token_type(token:str, expected_type:str) -> dict:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        token_type = decoded.get("type")
        if token_type != expected_type:
            raise JWTError(f"Invalid Token type: expected: {expected_type}")
        return decoded
    
    except ExpiredSignatureError:
        raise JWTError("Expired Token")
    except JWTError:
        raise
    except Exception as e:
        raise JWTError("Token verification failed")
    
def search_token(db: Session, token: str, type:TokenType):
    payload: dict = decode_token(token=token)
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token is missing JTI")
    
    if type == TokenType.invite.value:
        token_object = db.query(InviteToken).filter(InviteToken.jti == jti).first()
    
    elif type == TokenType.access.value:
         token_object = db.query(AccessToken).filter(AccessToken.jti == jti).first()
    
    else: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown token type"
        )
    return token_object
    
def verify_token(db: Session, token: str, type:TokenType):
    token_object = search_token(db=db, token=token, type=type)
    if not token_object:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found or already used",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    stored_hash = token_object.token_hash
    if not verify_password(password=token, hash=stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    return token_object


def get_token_record(db: Session, jti: str, type: TokenType):
    if type == TokenType.invite:
        token = db.query(InviteToken).filter(InviteToken.jti == jti).first()
    if type == TokenType.access:
        token = db.query(AccessToken).filter(AccessToken.jti == jti).first()
    if not token:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="Token does not exist")
    return token


def mark_token_used(db: Session, jti: str, type: TokenType):
    if type == TokenType.invite.value:
        token = db.query(InviteToken).filter(InviteToken.jti == jti).first()
    elif type == TokenType.access.value:
        token = db.query(AccessToken).filter(AccessToken.jti == jti).first()
    else:
        token = None

    if token is None:
        raise ValueError("Invalid token type")

    token.used_at = datetime.now()
    db.commit()
    db.refresh(token)

    return token
    
    

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





        



     


    


    
