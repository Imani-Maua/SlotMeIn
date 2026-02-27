"""
Validation functions for talent operations.

This module provides validation logic for creating and updating talent records,
including business rules for dates, names, and account status.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, date
from app.core.talents.schema import TalentIn, TalentUpdate
from app.database.models import Talent



def validate_talent_create(data: TalentIn, talent: Talent) -> None:
    """
    Validate talent creation data.

    Checks for:
    - Start date not too far in the future (max 7 days)
    - Start date not in the past
    - No duplicate email addresses
    - Non-empty first and last names

    Args:
        data: Talent input data to validate.
        talent: Existing talent with same email (if any).

    Raises:
        HTTPException: 400 if validation fails.
    """
    if talent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A talent with this email already exists"
        )
    
    if not data.firstname.strip() or not data.lastname.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty"
        )



def validate_talent_update(data: TalentUpdate, talent: Talent) -> None:
    """
    Validate talent update data.

    Checks for:
    - Talent exists
    - Reactivation is not allowed (business rule)
    - Names are not empty if provided

    Args:
        data: Partial talent data for update.
        talent: Existing talent record to update.

    Raises:
        HTTPException: 404 if talent not found, 403 if trying to reactivate.
    """
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talent not found"
        )

    if data.is_active is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reactivation is not allowed. Please create a new talent profile."
        )
    
    if data.firstname is not None and not data.firstname.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First name cannot be empty"
        )

    if data.lastname is not None and not data.lastname.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Last name cannot be empty"
        )


def talent_exists(talent: Talent) -> None:
    """
    Check if a talent record exists.

    Args:
        talent: Talent object or query result to check.

    Raises:
        HTTPException: 404 if talent not found.
    """
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Talent not found"
        )
