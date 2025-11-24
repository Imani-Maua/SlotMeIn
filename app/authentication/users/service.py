from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import insert
from datetime import timedelta
from jose import JWTError
from app.authentication.users.schema import CreateUser, UserOut, InviteTarget, NewPassword
from app.database.auth import User
from app.authentication.users.utils import lookup_user, generate_temporary_password, hash_password, invite_message, authenticate_user, user_is_active
from app.authentication.tokens.schema import Payload, TokenOut
from app.authentication.tokens.service import create_token, store_token, verify_token_type, verify_token, activate_user_account, mark_token_used
from app.core.utils.enums import TokenType


class UserService():


    @staticmethod
    def create_user(db:Session, user: CreateUser):
        username = f"{user.firstname.lower()}.{user.lastname.lower()}"
        user_exists = lookup_user(db=db, username=username)
        if user_exists:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists")
        
        temporary_password = generate_temporary_password()
        hashed_password = hash_password(temporary_password)
        stmt = (insert(User).values(username=username,
                                  email=user.email,
                                  firstname=user.firstname,
                                  lastname=user.lastname,
                                  user_role=user.user_role,
                                  pwd_hash=hashed_password).returning(User))
        result = db.execute(stmt)
        db.commit()

        user = result.scalar_one()
        return UserOut.model_validate(user)
    
    @staticmethod
    def invite_user(db: Session, id: InviteTarget):
        INVITE_EXPIRY_HOURS = 24
        user: User = lookup_user(db=db, user_id=id.user_id)
        payload = Payload(sub=user.username, id=user.id, email=user.email, role=user.user_role, type=TokenType.invite)
        token_expires = timedelta(hours=INVITE_EXPIRY_HOURS)
        invite_token = create_token(data=payload, expiry = token_expires)
        store_token(db=db, data=payload, jwt=invite_token)
        invite = invite_message(invite_token=invite_token, user=user)
        return invite
    
    @staticmethod
    def set_new_password(db: Session, data: NewPassword):
        decoded = verify_token_type(data.token, TokenType.invite.value)
        payload = Payload(**decoded)

        verify_token(db=db, token=data.token, type=payload.type)
        user_exists = lookup_user(db=db, user_id=payload.id)
        if not user_exists:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid account")
        hash_new_password = hash_password(data.new_password)
        activate_user_account(db=db, user_id=payload.id, hash=hash_new_password)
        mark_token_used(db=db, jti=payload.jti, type=payload.type)

        return {"message": "Account activated successfully"}
    
    @staticmethod
    def login(*, form_data:OAuth2PasswordRequestForm, db: Session):
        ACCESS_EXPIRY_DAYS = 4

        user: User = authenticate_user(db=db, username=form_data.username, password=form_data.password)
        
        payload = Payload(sub=user.username, id=user.id, email=user.email, role=user.user_role, type=TokenType.access)
        token_expires = timedelta(days=ACCESS_EXPIRY_DAYS)
        access_token = create_token(data=payload, expiry=token_expires)
        store_token(db=db, data=payload, jwt=access_token)
        return TokenOut(access_token=access_token,token_type="bearer",role=user.user_role)
    
    
        


        


        
        
        



        
    

        
