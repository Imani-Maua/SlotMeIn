"""
API routes for user management.

All mutating routes require authentication. The list_users and send_invite
endpoints are restricted to superusers only.
"""

from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated, List
from app.authentication.users.schema import CreateUser, InviteTarget, NewPassword, UserOut
from app.authentication.tokens.schema import TokenIn, TokenOut
from app.database.session import session
from app.authentication.users.service import UserService
from app.authentication.utils.auth_utils import get_current_user
from app.database.auth import User

auth_router = APIRouter(tags=['Users'])


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that raises 403 if the caller is not a superuser."""
    if current_user.user_role != "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can access this endpoint."
        )
    return current_user


@auth_router.post("/create")
def create_user(user: Annotated[CreateUser, Body()],
                db: Annotated[Session, Depends(session)]):
    return UserService.create_user(db=db, user=user)


@auth_router.get("/list", response_model=List[UserOut])
def list_users(
    _: Annotated[User, Depends(require_superuser)],
    db: Annotated[Session, Depends(session)]
):
    """List all users. Superuser only."""
    users = db.query(User).order_by(User.id).all()
    return [UserOut.model_validate(u) for u in users]


@auth_router.post("/send_invite")
def invite_user(
    user_id: Annotated[InviteTarget, Body()],
    _: Annotated[User, Depends(require_superuser)],
    db: Annotated[Session, Depends(session)]
):
    """Send an invitation email to a user. Superuser only."""
    return UserService.invite_user(db=db, id=user_id)


@auth_router.post("/set_new_password")
def accept_invite(data: Annotated[NewPassword, Body()],
                  db: Annotated[Session, Depends(session)]):
    return UserService.set_new_password(data=data, db=db)


@auth_router.post("/login_token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: Annotated[Session, Depends(session)]):
    login = UserService.login(form_data=form_data, db=db)
    return login


@auth_router.get("/me")
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return {"firstname": current_user.firstname, "role": current_user.user_role}