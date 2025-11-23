from pydantic import BaseModel,EmailStr, ConfigDict, field_validator
from datetime import date
from app.core.utils.enums import Role, ContractType


class TalentIn(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    tal_role: Role
    contract_type: ContractType
    start_date: date

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_validator("firstname", "lastname", mode="before")
    @classmethod
    def capitalize_name(cls, value):
        if not isinstance(value, str):
            return value
        return value.capitalize()
    
    @field_validator("email", mode="before")
    @classmethod
    def lower_email(cls, value):
        if not isinstance(value, str):
            return value
        return value.lower()
    



class TalentUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: EmailStr | None = None
    tal_role: Role | None = None
    contract_type: ContractType | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_validator("firstname", "lastname", mode="before")
    @classmethod
    def capitalize_name(cls, value):
        if not isinstance(value, str):
            return value
        if value is None:
            return value
        return value.capitalize()
    
    @field_validator("email", mode="before")
    @classmethod
    def lower_email(cls, value):
        if not isinstance(value, str):
            return value
        if value is None:
            return value
        return value.lower()

class TalentOut(BaseModel):
    firstname: str
    lastname: str
    tal_role: str
    contract_type: str
    hours: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    
class TalentRead(BaseModel):
    firstname: str
    lastname: str
    tal_role: str

    model_config = ConfigDict(from_attributes=True)