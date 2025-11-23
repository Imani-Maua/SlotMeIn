from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from app.auth.services.security import required_roles
from app.auth.schema import UserRole
from app.database.session import session
from app.core.constraints.constraint_rules.schema import ConstraintRuleIn
from app.core.constraints.constraint_rules.services.services import ConstraintRuleService

constraint_rules = APIRouter(tags=['Constraint Rules'])

@constraint_rules.post("/create")
def create_constraint_rule(db: Annotated[Session, Depends(session)],
                      data: Annotated[ConstraintRuleIn, Body()],
                     # _:str= Depends(required_roles(UserRole.admin, UserRole.manager))
                      ):
    constraint_rule = ConstraintRuleService().create_rules(db=db, data=data)
    return constraint_rule

@constraint_rules.delete("/delete/{rule_id}", status_code=204)
def delete_constraint_rule(db: Annotated[Session, Depends(session)],
                              rule_id: int,
                            # _: str= Depends(required_roles(UserRole.admin, UserRole.manager))
                              ):
    ConstraintRuleService().delete_rules(db=db, rule_id=rule_id)