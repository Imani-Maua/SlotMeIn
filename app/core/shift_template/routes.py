"""
API routes for shift template management.

This module provides REST API endpoints for creating, reading, updating,
and deleting shift templates (time ranges for shifts within a period).
"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import time

from app.database.session import session
from app.database.auth import User
from app.core.shift_template.schema import TemplateIn, TemplateUpdate, TemplateOut
from app.core.shift_template.services.service import TemplateService, get_template, get_all_templates
from app.authentication.utils.auth_utils import get_current_user


shift_templates = APIRouter(tags=["Shift Templates"])


@shift_templates.post("/create", response_model=TemplateOut)
def create_template(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: Annotated[TemplateIn, Body()]
):
    """
    Create a new shift template.

    Requires authentication. Creates a template defining shift times within a period.
    Validates that times fall within the period and meet minimum shift length (4 hours).

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        data: Template data including period_id, shift times, and staffing requirements.

    Returns:
        TemplateOut: Created shift template record.

    Raises:
        HTTPException: 400 if validation fails (invalid times, period not found, etc.).
    """
    shift_template = TemplateService().create_template(db=db, data=data)
    return shift_template

@shift_templates.put("/update/{template_id}", response_model=TemplateOut)
def update_template(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    template_id: int,
    update_data: Annotated[TemplateUpdate, Body()]
):
    """
    Update an existing shift template.

    Requires authentication. Supports partial updates. Validates that any time
    changes maintain minimum shift length and fall within the period.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        template_id: ID of the template to update.
        update_data: Partial template data to update.

    Returns:
        TemplateOut: Updated shift template record.

    Raises:
        HTTPException: 404 if template not found, 400 if validation fails.
    """
    updated_template = TemplateService().update_template(db=db, data=update_data, template_id=template_id)
    return updated_template

@shift_templates.delete("/delete/{template_id}", status_code=204, response_model=None)
def delete_template(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    template_id: int
):
    """
    Delete a shift template.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        template_id: ID of the template to delete.

    Raises:
        HTTPException: 404 if template not found.
    """
    TemplateService().delete_template(db=db, template_id=template_id)

@shift_templates.get("/retrieve_template/{template_id}", response_model=TemplateOut)
def retrieve_template(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    template_id: int
):
    """
    Retrieve a single shift template by ID.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        template_id: ID of the template to retrieve.

    Returns:
        TemplateOut: Shift template record.

    Raises:
        HTTPException: 404 if template not found.
    """
    return get_template(db=db, id=template_id)


@shift_templates.get("/retrieve_all_templates", response_model=list[TemplateOut])
def retrieve_templates(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    shift_name: str | None = None,
    shift_start: time | None = None,
    shift_end: time | None = None
):
    """
    Retrieve all shift templates with optional filtering.

    Requires authentication. Supports filtering by shift period name and times.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        shift_name: Optional filter by shift period name.
        shift_start: Optional filter by shift start time.
        shift_end: Optional filter by shift end time.

    Returns:
        List of TemplateOut objects matching the filters.

    Raises:
        HTTPException: 404 if no templates found.
    """
    return get_all_templates(
        db=db, 
        shift_name=shift_name, 
        shift_start=shift_start, 
        shift_end=shift_end
    )
