from fastapi import APIRouter, Depends,Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from app.authentication.users.schema import CreateUser, InviteTarget, NewPassword
from app.authentication.tokens.schema import TokenIn, TokenOut
from app.database.session import session
from app.authentication.users.service import UserService

auth_router = APIRouter(tags=['Users'])

@auth_router.post("/create")
def create_user(user: Annotated[CreateUser, Body()],
                db: Annotated[Session, Depends(session)]):
    return UserService.create_user(db=db, user=user)


@auth_router.post("/send_invite")
def invite_user(user_id:Annotated[InviteTarget, Body()], 
                      db: Annotated[Session, Depends(session)]
                      ):
    return UserService.invite_user(db=db, id=user_id)


@auth_router.post("/set_new_password")
def accept_invite(data: Annotated[NewPassword, Body ()], 
                        db: Annotated[Session, Depends(session)]):
    return UserService.set_new_password(data=data, db=db)

@auth_router.post("/login_token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                  db: Annotated[Session, Depends(session)]):
    login = UserService.login(form_data=form_data, db=db)
    return login
  
  
 