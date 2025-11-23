from itertools import product
from app.database.models import TalentConstraint
from app.core.constraints.constraint_rules.schema import  ConstraintRuleIn, ConstraintRuleCreate
from app.core.utils.enums import ConstraintType




def generate_rule_combinations(data: ConstraintRuleIn) -> list[ConstraintRuleCreate]:
        days = [day.value for day in (data.day or [])] or [None]
        shifts = [shift.value for shift in (data.shifts or [])] or [None]

        rules = []

        for day, shift in product(days, shifts):
            rules.append(ConstraintRuleCreate(
                constraint_id = data.constraint_id,
                day = day,
                shifts = shift
            ))
        
        return rules

def rules_configuration(constraint: TalentConstraint) -> dict:

        CONSTRAINT_VALIDATION_RULES = {
        ConstraintType.AVAILABILITY.value: {"allow_day": True, "allow_shift": False},
        ConstraintType.SHIFT_RESTRICTION.value: {"allow_day": False, "allow_shift": True},
        ConstraintType.COMBINATION.value: {"allow_day": True, "allow_shift": True, "require_both": True}
    }
        
        rules_config = CONSTRAINT_VALIDATION_RULES.get(constraint.type)

        if not rules_config:
            raise ValueError(f"Unknown constraint type: {constraint.type}")

        return rules_config  

