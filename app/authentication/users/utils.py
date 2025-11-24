from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import hashlib
import string
import secrets
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.models import Base
from sqlalchemy.exc import SQLAlchemyError
from app.database.auth import User
from app.config.config import Settings
from app.authentication.tokens.schema import Payload
from app.authentication.tokens.service import decode_token


settings = Settings()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
SECRET_KEY = settings.KEY
algorithm = "HS256"
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = int(settings.SMTP_PORT)
SMTP_USER = settings.SMTP_USER
SMTP_PASS = settings.SMTP_PASS

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
    token_data: Payload = decode_token(token)
    user = lookup_user(db=db, user_id=token_data.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user

def user_is_active(user: Annotated[User, Depends(get_user_from_token)]):
    if user.is_active is not True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user



def generate_temporary_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation
    temporary = ''.join(secrets.choice(alphabet) for _ in range(12))
    return temporary

def hash_password(password: str) -> str:
    prehash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(prehash)

def verify_password(password: str, hash: str) -> bool:
    prehash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.verify(prehash, hash)

def send_email(to_email:str, subject: str, body: str):

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
            print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise



def invite_message(invite_token: str, user: User):
    
    INVITE_EXPIRY_HOURS = 24
    invite_link = f"https://shiftly.app/register?token={invite_token}"
    name = user.username.split(".")[0].capitalize()

    subject = "You've been invited to Shiftly!"
    body = f""" 
Hello {name},
You’ve been invited to join Shiftly as a {user.user_role}.

    Registration link (valid {INVITE_EXPIRY_HOURS} h): {invite_link}

    Please login and change your password immediately after first access.
    """

    try:
        send_email(to_email=user.email, subject=subject, body=body)
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email: {e}")
    
    return {"message": f"Invite sent to {user.email}"}






