from fastapi import Depends, Body,APIRouter
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import time
from app.database.session import session
from app.core.shift_period.schema import ShiftPeriodIn, ShiftPeriodUpdate
from app.auth.services.security import required_roles
from app.auth.schema import UserRole
from app.core.shift_period.services.services import ShiftPeriodService, get_all_periods, get_period

shift_period = APIRouter(tags=["Shift Period"])


# change the UserRole.enum values
@shift_period.post("/create")
def create_shift_period(db: Annotated[Session, Depends(session)],
                              data: Annotated[ShiftPeriodIn, Body()],
                             _: str = Depends(required_roles(UserRole.superuser))
                             ):


    shift_period = ShiftPeriodService().create_shift_period(db=db, data=data)
    return shift_period

  
@shift_period.patch("/update/{period_id}")
def update_shift_period(db: Annotated[Session,  Depends(session)],
                              period_id: int,
                              update_data: Annotated[ShiftPeriodUpdate, Body()],
                              _: str= Depends(required_roles(UserRole.admin, UserRole.manager))
                                ):
    

    updated_shift_period = ShiftPeriodService().update_shift_period(db=db, data=update_data, period_id=period_id)
    return updated_shift_period

@shift_period.delete("/delete/{period_id}", status_code=204)
def delete_shift_period(db: Annotated[Session, Depends(session)],
                              period_id: int,
                             _: str= Depends(required_roles(UserRole.admin, UserRole.manager))
                              ):
    ShiftPeriodService().delete_shift_period(db=db, period_id=period_id)

@shift_period.get("/retrive_period/{period_id}")
def retrieve_period(db:Annotated[Session, Depends(session)], period_id: int):
    return get_period(db=db, id=period_id)

@shift_period.get("/retrieve_all_periods")
def retrieve_periods(db: Annotated[Session, Depends(session)],
                    shift_name: str | None = None,
                   start_time: time | None = None,
                   end_time: time | None = None):
    return get_all_periods(db=db, shift_name=shift_name, start_time=start_time, end_time=end_time)
   