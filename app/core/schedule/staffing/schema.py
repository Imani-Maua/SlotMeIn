from pydantic import BaseModel, Field


class StaffingRuleResponse(BaseModel):
    role: str
    tier: str
    count: int

    class Config:
        from_attributes = True


class StaffingRuleUpdate(BaseModel):
    count: int = Field(..., ge=0, le=20)
