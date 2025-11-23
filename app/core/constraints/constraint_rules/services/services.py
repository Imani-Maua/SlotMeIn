from sqlalchemy.orm import Session
from app.core.utils.crud import CRUDBase
from app.database.models import ConstraintRule, TalentConstraint
from app.core.constraints.constraint_rules.schema import  ConstraintRuleCreate, ConstraintRuleUpdate, ConstraintRuleIn, ConstraintRuleOut
from app.core.constraints.constraint_rules.utils import generate_rule_combinations
from app.core.constraints.constraint_rules.services.validators import evaluate_existing_rules, validate_constraint_rules, context_finder, rule_exists
from app.core.constraints.constraint_rules.utils import rules_configuration



class ConstraintRuleService(CRUDBase[ConstraintRule, ConstraintRuleIn, ConstraintRuleUpdate]):

    def __init__(self):
        super().__init__(ConstraintRule)
       
    
    def create_rules(self, db: Session, data:ConstraintRuleIn):
        constraint = db.query(TalentConstraint).filter(
            TalentConstraint.id == data.constraint_id).first()
        
        rules_config = rules_configuration(constraint=constraint)
        
        ctx = context_finder(db=db, data=data, rules_config=rules_config, constraint=constraint)
        validate_constraint_rules(ctx)
        evaluate_existing_rules(ctx)
        rules_to_process: list[ConstraintRuleCreate] = generate_rule_combinations(data)

        constraint.is_active = True
        
        created_rules: list[ConstraintRule] = self.batch_create(db=db, objs_in=rules_to_process)
        
        return [ConstraintRuleOut.model_validate(rule) for rule in created_rules]

    def delete_rules(self, db: Session, rule_id: int):
        rule = db.query(ConstraintRule).filter(ConstraintRule.id == rule_id).first()
        rule_exists(rule)
        self.delete(db=db, id=rule_id)

def get_rule(db: Session, id: int):
    rule = db.query(ConstraintRule).filter(ConstraintRule.id == id)
    rule_exists(rule)
    return ConstraintRuleOut.model_validate(rule)




        