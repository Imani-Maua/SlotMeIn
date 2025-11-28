from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, date
from typing import Optional

class Payload(BaseModel):
    sub: str
    id: int
    email: EmailStr
    role: str
    type: str
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None

class Token(BaseModel):
    id: int
    user_id: int
    token_hash: str
    jti: str
    expires_at: date
    used_at: date
    created_at: date

    model_config = ConfigDict(use_enum_values=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenIn:
    token:str