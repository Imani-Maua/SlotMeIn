from fastapi import HTTPException, status
from app.database.models import Talent, TalentConstraint


def validate_constraint_input(talent: Talent, constraint: TalentConstraint, constraint_type: str):
    if not talent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent does not exist")
    if not talent.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Talent is inactive")
    if talent.contract_type == "full-time" and constraint_type in ("availability", "combination"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full-time staff can only restrict shifts, not working days or specific schedules",
        )
    if constraint:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Constraint already exists")


def constraint_exists(constraint: TalentConstraint):
        if not constraint: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constraint does not exist")
       
    