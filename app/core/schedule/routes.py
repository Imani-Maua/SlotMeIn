from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import Annotated
import asyncpg
from app.database.database import get_db
from app.database.session import session

from app.core.schedule.schema import inputDate

from app.core.schedule.services.service import ScheduleService



schedule = APIRouter(tags=["Schedule"])


@schedule.post("/generate")
async def generate_schedule(db: Annotated[asyncpg.Connection, Depends(get_db)],
                            start_date: Annotated[inputDate, Body()]
                             ):
    schedule = await ScheduleService.generate_schedule(start_date)
    return schedule


@schedule.get("/view/{week_start}")
async def view_schedule(db: Annotated[Session, Depends(session)],
                        week_start: date):
    result = ScheduleService(db)
    schedule = await result.get_schedule_by_week_start(week_start)
    return schedule
    #set this such that you can only give a date that is on Sunday/Monday depending on when week_start is












