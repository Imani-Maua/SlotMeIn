from fastapi import Depends, Body,APIRouter
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import time
from app.database.session import session
from app.core.shift_period.schema import ShiftPeriodIn, ShiftPeriodUpdate, ShiftOut, OneShiftOut

from app.core.shift_period.services.services import ShiftPeriodService, get_all_periods, get_period

shift_period = APIRouter(tags=["Shift Period"])



@shift_period.post("/create", response_model=ShiftOut)
def create_shift_period(db: Annotated[Session, Depends(session)],
                              data: Annotated[ShiftPeriodIn, Body()]
                            
                             ):


    return ShiftPeriodService().create_shift_period(db=db, data=data)
    

  
@shift_period.patch("/update/{period_id}", response_model=ShiftOut)
def update_shift_period(db: Annotated[Session,  Depends(session)],
                              period_id: int,
                              update_data: Annotated[ShiftPeriodUpdate, Body()]
                           
                                ):
    

    return ShiftPeriodService().update_shift_period(db=db, data=update_data, period_id=period_id)
   

@shift_period.delete("/delete/{period_id}", status_code=204, response_model=None)
def delete_shift_period(db: Annotated[Session, Depends(session)],
                              period_id: int
                         
                              ):
    return ShiftPeriodService().delete_shift_period(db=db, period_id=period_id)

@shift_period.get("/retrive_period/{period_id}", response_model=OneShiftOut)
def retrieve_period(db:Annotated[Session, Depends(session)], period_id: int):
    return get_period(db=db, id=period_id)

@shift_period.get("/retrieve_all_periods", response_model=list[ShiftOut])
def retrieve_periods(db: Annotated[Session, Depends(session)],
                    shift_name: str | None = None,
                   start_time: time | None = None,
                   end_time: time | None = None):
    return get_all_periods(db=db, shift_name=shift_name, start_time=start_time, end_time=end_time)
   