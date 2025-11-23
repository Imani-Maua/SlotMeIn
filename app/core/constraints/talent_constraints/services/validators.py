from fastapi import HTTPException, status
from datetime import time
from app.database.models import Talent, TalentConstraint
from app.core.constraints.talent_constraints.schema import ConstraintIn


def validate_constraint_input(talent: Talent, constraint: TalentConstraint):
    if not talent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talent does not exist")
    if not talent.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Talent is inactive")
    if constraint:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Constraint already exists")


def constraint_exists(constraint: TalentConstraint):
        if not constraint: 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constraint does not exist")
       
    