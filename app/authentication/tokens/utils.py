from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.exc import DatabaseError
from datetime import datetime, timedelta
from jose import jwt,JWTError, ExpiredSignatureError
import uuid
from typing import Annotated
from app.config.config import Settings
from app.auth.utils.utils import hash_password
from app.auth.token.auth_schema import Payload, Token
from app.database.auth import InviteToken, AccessToken, User
from app.auth.utils.utils import insert_to_db
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