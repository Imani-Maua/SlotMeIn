from pydantic import BaseModel, ConfigDict, field_validator
from datetime import time
from app.core.utils.enums import Shifts


 
class ShiftPeriodIn(BaseModel):
    shift_name: Shifts
    start_time: time
    end_time: time

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    @field_validator("shift_name", mode="before")
    @classmethod
    def normalize_shift_name(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class ShiftPeriodUpdate(BaseModel):
    start_time: time  | None = None
    end_time: time  | None = None

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

   
class ShiftOut(BaseModel):
    shift_name: Shifts
    start_time: time
    end_time: time

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    



    