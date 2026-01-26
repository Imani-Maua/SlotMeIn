"""
API routes for talent management.

This module provides REST API endpoints for creating, reading, updating,
and managing talent/employee records.
"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated, Union, List
from app.core.talents.services.service import TalentService, get_talent, get_all_talents
from app.core.talents.schema import TalentIn, TalentUpdate, TalentOut
from app.database.session import session
from app.database.auth import User
from app.database.models import Talent
from app.authentication.utils.auth_utils import get_current_user


talents = APIRouter(tags=["Talents"])



@talents.post("/create", response_model=TalentOut)
def create_talent(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: Annotated[TalentIn, Body()]
):
    """
    Create a new talent record.

    Requires authentication. Creates a talent profile with automatic contract hour
    calculation based on contract type.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        data: Talent creation data including name, email, role, and contract details.

    Returns:
        TalentOut: Created talent record with all fields.

    Raises:
        HTTPException: 400 if validation fails (duplicate email, invalid dates, etc.).
    """
    talents = TalentService().create_talent(db=db, data=data)
    return talents
  
@talents.put("/update/{talent_id}", response_model=TalentOut)
def update_talent(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    talent_id: int,
    data: Annotated[TalentUpdate, Body()]
):
    """
    Update an existing talent record.

    Requires authentication. Supports partial updates. Deactivating a talent
    automatically sets their end date.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        talent_id: ID of the talent to update.
        data: Partial talent data to update.

    Returns:
        TalentOut: Updated talent record.

    Raises:
        HTTPException: 404 if talent not found, 403 if trying to reactivate.
    """
    talent = TalentService().update_talent(db, talent_id, data)
    return talent

@talents.get("/retrieve_talents", response_model=list[TalentOut])
def retrieve_all_talents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)], 
    name: str | None = None, 
    tal_role: str | None = None,
    contract_type: str | None = None,
    is_active: bool | None = None
):
    """
    Retrieve all talents with optional filtering.

    Requires authentication. Supports filtering by name, role, contract type,
    and active status.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        name: Optional filter by first or last name (partial match).
        tal_role: Optional filter by role.
        contract_type: Optional filter by contract type.
        is_active: Optional filter by active status.

    Returns:
        List of TalentOut objects matching the filters.

    Raises:
        HTTPException: 404 if no talents found.
    """
    return get_all_talents(db, name=name, tal_role=tal_role, contract_type=contract_type, is_active=is_active)

@talents.get("/retrieve_talent/{talent_id}", response_model=TalentOut)
def retrieve_a_talent(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    talent_id: int
):
    """
    Retrieve a single talent by ID.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        talent_id: ID of the talent to retrieve.

    Returns:
        TalentOut: Talent record with all fields.

    Raises:
        HTTPException: 404 if talent not found.
    """
    return get_talent(db=db, id=talent_id)
