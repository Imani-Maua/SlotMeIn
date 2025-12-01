"""
API routes for talent constraint management.

This module provides REST API endpoints for creating, reading, and deleting
talent constraints (availability restrictions for specific talents).
"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from app.core.constraints.talent_constraints.services.services import TalentConstraintService, get_all_constraints, get_constraint
from app.database.session import session
from app.database.auth import User
from app.core.constraints.talent_constraints.schema import ConstraintIn, ConstraintOut
from app.authentication.utils.auth_utils import get_current_user



talent_constraints = APIRouter(tags=["Talent Constraints"])



@talent_constraints.post("/create", response_model=ConstraintOut)
def create_constraint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: Annotated[ConstraintIn, Body()]
):
    """
    Create a new talent constraint.

    Requires authentication. Creates a constraint defining when a talent is
    unavailable or has preferences (e.g., cannot work Mondays).

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        data: Constraint data including talent_id and constraint type.

    Returns:
        ConstraintOut: Created constraint record.

    Raises:
        HTTPException: 404 if talent not found, 400 if talent inactive, 403 if constraint exists.
    """
    constraint = TalentConstraintService().create_constraint(db=db, data=data)
    return constraint

@talent_constraints.delete("/delete/{constraint_id}", status_code=204)
def delete_constraint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    constraint_id: int
):
    """
    Delete a talent constraint.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        constraint_id: ID of the constraint to delete.

    Raises:
        HTTPException: 404 if constraint not found.
    """
    TalentConstraintService().delete_constraint(db=db, constraint_id=constraint_id)

@talent_constraints.get("/retrieve_constraint/{constraint_id}", response_model=ConstraintOut)
def retrieve_constraint(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    constraint_id: int
):
    """
    Retrieve a single talent constraint by ID.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        constraint_id: ID of the constraint to retrieve.

    Returns:
        ConstraintOut: Constraint record with talent info and rules.

    Raises:
        HTTPException: 404 if constraint not found.
    """
    return get_constraint(db=db, id=constraint_id)

@talent_constraints.get("/retrieve_all_constraints", response_model=list[ConstraintOut])
def retrieve_all_constraints(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    constraint_id: int | None = None,
    talent_id: int | None = None,
    tal_role: str | None = None,
    name: str | None = None,
    contract_type: str | None = None,
    is_active: bool | None = None
):
    """
    Retrieve all talent constraints with optional filtering.

    Requires authentication. Supports filtering by constraint ID, talent attributes,
    and active status.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        constraint_id: Optional filter by constraint ID.
        talent_id: Optional filter by talent ID.
        tal_role: Optional filter by talent role.
        name: Optional filter by talent name.
        contract_type: Optional filter by talent contract type.
        is_active: Optional filter by constraint active status.

    Returns:
        List of ConstraintOut objects matching the filters.

    Raises:
        HTTPException: 404 if no constraints found.
    """
    return get_all_constraints(
        db=db,
        constraint_id=constraint_id,
        talent_id=talent_id,
        tal_role=tal_role,
        name=name,
        contract_type=contract_type,
        is_active=is_active
    )


