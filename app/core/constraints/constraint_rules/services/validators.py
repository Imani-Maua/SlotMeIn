from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.constraints.constraint_rules.schema import ConstraintRuleIn
from app.database.models import TalentConstraint, ConstraintRule
from app.core.utils.enums import ConstraintType



def context_finder(*, db: Session, data: ConstraintRuleIn, rules_config: dict, constraint:TalentConstraint ) -> dict:

        context = {
            "db": db,
            "data": data,
            "rules_config": rules_config,
            "constraint": constraint
        }

        return context
                         
 

def validate_constraint_rules(context: dict):

        data: ConstraintRuleIn = context["data"]
        rules_config: dict = context["rules_config"]
        constraint: TalentConstraint = context["constraint"]
        
        has_day = bool(data.day)
        has_shifts = bool(data.shifts)
        if not constraint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constraint does not exist")
        
        if constraint.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                detail="Constraint already exists. Click here to update")

        if not has_day and not has_shifts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Must provide at least one day or shift")

        if not rules_config.get("allow_shift") and has_shifts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Shifts are not allowed for Availability constraints")
        
        if not rules_config.get("allow_day") and has_day:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Days are not allowed for Shift restriction constraints")
        
        if rules_config.get("require_both") and (not has_day or not has_shifts):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Combination constraints require both day and shifts")
    
def evaluate_existing_rules(context: dict):

        db: Session = context["db"]
        data: ConstraintRuleIn = context["data"]
        constraint: TalentConstraint = context["constraint"]

        CONSTRAINT_FILTERS = {
            ConstraintType.AVAILABILITY.value: lambda data: ConstraintRule.day.in_([day.value for day in (data.day or [])]),
            ConstraintType.SHIFT_RESTRICTION.value: lambda data: ConstraintRule.shifts.in_([shift.value for shift in (data.shifts or [])]),
            ConstraintType.COMBINATION.value: lambda data: and_(ConstraintRule.shifts.in_([shift.value for shift  in data.shifts or []]),
                                                          ConstraintRule.day.in_([day.value for day in data.day or []]))
        }

        if not data.day and not data.shifts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one day or shift required")

        filter_expression = CONSTRAINT_FILTERS[constraint.type](data)
        existing_rules = db.query(ConstraintRule).filter(ConstraintRule.constraint_id == data.constraint_id, filter_expression).first()

        if existing_rules:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Constraint rule exists")
        


def rule_exists(rule: ConstraintRule):
     if not rule:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Constraint rule does not exist")