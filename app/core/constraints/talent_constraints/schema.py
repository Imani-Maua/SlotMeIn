from pydantic import BaseModel, ConfigDict
from app.core.utils.enums import ConstraintType, Days, Shifts


class Talent(BaseModel):
    id: int
    firstname: str
    lastname: str
    
    model_config = ConfigDict(from_attributes=True)

class Rules(BaseModel):
    day: str
    shifts: str

    model_config = ConfigDict(from_attributes=True, exclude_none=True)

class ConstraintIn(BaseModel):
    talent_id: int 
    type: ConstraintType

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

class ConstraintUpdate(BaseModel):
    is_active: bool
    days: Days | None = None
    shifts: Shifts | None = None

class ConstraintOut(BaseModel):
    talent: Talent
    type: ConstraintType
    is_active: bool
    rules: list[Rules]

    model_config = ConfigDict(use_enum_values=True, from_attributes=True, exclude_none=True)


