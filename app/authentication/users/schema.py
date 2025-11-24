from pydantic import BaseModel, EmailStr, field_validator
from app.core.utils.enums import UserRole



class CreateUser(BaseModel):
    firstname:str
    lastname: str
    user_role: UserRole
    email: EmailStr

    @field_validator("firstname", "lastname", mode="before")
    @classmethod
    def normalize_name(cls, input:str):
        return input.strip().capitalize()
    
    @field_validator("user_role", "email", mode="before")
    @classmethod
    def normalize_role(cls, input:str):
        return input.strip().lower()

class UserOut(BaseModel):
    username: str
    email: EmailStr
    user_role: str
    is_active: bool

class InsertUser(BaseModel):
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    user_role: str
    pwd_hash: str

class InviteTarget(BaseModel):
    user_id: int

class NewPassword(BaseModel):
    token: str
    new_password: str
