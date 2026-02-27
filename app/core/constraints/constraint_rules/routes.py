"""
API routes for constraint rule management.

This module provides REST API endpoints for creating and deleting constraint rules
(specific days/shifts that a talent is unavailable).
"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from app.database.session import session
from app.database.auth import User
from app.core.constraints.constraint_rules.schema import ConstraintRuleIn, ConstraintRuleOut
from app.core.constraints.constraint_rules.services.services import ConstraintRuleService
from app.authentication.utils.auth_utils import get_current_user

constraint_rules = APIRouter(tags=['Constraint Rules'])

@constraint_rules.post("/create", response_model=list[ConstraintRuleOut])
def create_constraint_rule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: Annotated[ConstraintRuleIn, Body()]
):
    """
    Create a new constraint rule.

    Requires authentication. Creates a rule specifying which days/shifts a talent
    is unavailable (e.g., cannot work Monday mornings).

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        data: Rule data including constraint_id, days, and shifts.

    Returns:
        ConstraintRuleOut: Created constraint rule record.

    Raises:
        HTTPException: 404 if constraint not found, 409 if rule already exists,
                      400 if validation fails.
    """
    constraint_rule = ConstraintRuleService().create_rules(db=db, data=data)
    return constraint_rule

@constraint_rules.delete("/delete/{rule_id}", status_code=204)
def delete_constraint_rule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    rule_id: int
):
    """
    Delete a constraint rule.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        rule_id: ID of the rule to delete.

    Raises:
        HTTPException: 404 if rule not found.
    """
    ConstraintRuleService().delete_rules(db=db, rule_id=rule_id)