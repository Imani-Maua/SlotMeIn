from pydantic import BaseModel
from datetime import date, time
from typing import Optional


class inputDate(BaseModel):
    start_date: date


class AssignmentBase(BaseModel):
    talent_id: int
    date_of: date
    start_time: time
    end_time: time
    shift_name: Optional[str] = None


class AssignmentIn(AssignmentBase):
    schedule_id: int


class AssignmentUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    shift_name: Optional[str] = None


class AssignmentOut(AssignmentBase):
    id: int
    schedule_id: Optional[int] = None
    shift_hours: Optional[float] = None

    class Config:
        from_attributes = True


class ScheduleOut(BaseModel):
    id: int
    week_start: date
    week_end: date
    status: str
    assignments: list[AssignmentOut] = []

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    week_start: date
    week_end: date
    assignments: list[AssignmentBase]
    status: str = "final"   # 'draft' or 'final'


class StatusUpdate(BaseModel):
    status: str  # 'draft' or 'final'


class ValidationRequest(BaseModel):
    talent_id: int
    date_of: date
    start_time: time
    end_time: time
    shift_name: Optional[str] = None
    schedule_id: Optional[int] = None
