"""
API routes for shift period management.

This module provides REST API endpoints for creating, reading, updating,
and deleting shift periods (the overall time windows for scheduling).
"""

from fastapi import Depends, Body, APIRouter
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import time
from app.database.session import session
from app.database.auth import User
from app.core.shift_period.schema import ShiftPeriodIn, ShiftPeriodUpdate, ShiftOut, OneShiftOut
from app.core.shift_period.services.services import ShiftPeriodService, get_all_periods, get_period
from app.authentication.utils.auth_utils import get_current_user

shift_period = APIRouter(tags=["Shift Period"])



@shift_period.post("/create", response_model=ShiftOut)
def create_shift_period(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: Annotated[ShiftPeriodIn, Body()]
):
    """
    Create a new shift period.

    Requires authentication. Creates a shift period defining the overall time window
    for scheduling (e.g., "Morning Shift" from 6:00 AM to 2:00 PM).

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        data: Shift period data including name, start/end times, and dates.

    Returns:
        ShiftOut: Created shift period record.

    Raises:
        HTTPException: 400 if validation fails (invalid times, dates, etc.).
    """
    return ShiftPeriodService().create_shift_period(db=db, data=data)
    

  
@shift_period.patch("/update/{period_id}", response_model=ShiftOut)
def update_shift_period(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    period_id: int,
    update_data: Annotated[ShiftPeriodUpdate, Body()]
):
    """
    Update an existing shift period.

    Requires authentication. Supports partial updates.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        period_id: ID of the shift period to update.
        update_data: Partial shift period data to update.

    Returns:
        ShiftOut: Updated shift period record.

    Raises:
        HTTPException: 404 if period not found, 400 if validation fails.
    """
    return ShiftPeriodService().update_shift_period(db=db, data=update_data, period_id=period_id)
   

@shift_period.delete("/delete/{period_id}", status_code=204, response_model=None)
def delete_shift_period(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    period_id: int
):
    """
    Delete a shift period.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        period_id: ID of the shift period to delete.

    Raises:
        HTTPException: 404 if period not found.
    """
    return ShiftPeriodService().delete_shift_period(db=db, period_id=period_id)

@shift_period.get("/retrieve_period/{period_id}", response_model=OneShiftOut)
def retrieve_period(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    period_id: int
):
    """
    Retrieve a single shift period by ID.

    Requires authentication.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        period_id: ID of the shift period to retrieve.

    Returns:
        OneShiftOut: Shift period record with templates.

    Raises:
        HTTPException: 404 if period not found.
    """
    return get_period(db=db, id=period_id)

@shift_period.get("/retrieve_all_periods", response_model=list[ShiftOut])
def retrieve_periods(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    shift_name: str | None = None,
    start_time: time | None = None,
    end_time: time | None = None
):
    """
    Retrieve all shift periods with optional filtering.

    Requires authentication. Supports filtering by name and times.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        shift_name: Optional filter by shift period name.
        start_time: Optional filter by start time.
        end_time: Optional filter by end time.

    Returns:
        List of ShiftOut objects matching the filters.

    Raises:
        HTTPException: 404 if no periods found.
    """
    return get_all_periods(db=db, shift_name=shift_name, start_time=start_time, end_time=end_time)
   