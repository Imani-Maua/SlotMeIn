from pydantic import BaseModel, ConfigDict, field_validator
from datetime import time
from app.core.utils.enums import TemplateRole, Shifts



class TemplateIn(BaseModel):
    period_id: int
    shift_start: time
    shift_end: time
    role: TemplateRole

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class TemplateUpdate(BaseModel):
    shift_start: time | None = None
    shift_end: time | None = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class PeriodOut(BaseModel):
    shift_name: Shifts
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_validator("shift_name", mode="before")
    @classmethod

    def normalize_shift_name(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class TemplateOut(BaseModel):
    period: PeriodOut
    shift_start: time 
    shift_end: time 

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)