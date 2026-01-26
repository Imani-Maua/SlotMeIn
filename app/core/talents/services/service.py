"""
Talent service layer for managing employee/talent records.

This module provides CRUD operations for talents including creation, updates,
retrieval with filtering, and contract hour management.
"""

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Union, List
from app.core.talents.schema import TalentIn, TalentUpdate, TalentOut
from app.core.utils.crud import CRUDBase
from app.database.models import Talent
from app.core.talents.services.validator import validate_talent_create, validate_talent_update, talent_exists
from app.core.talents.utils import set_contract_hours, search_filters


class TalentService(CRUDBase[Talent, TalentIn, TalentUpdate]):
    """
    Service class for managing talent records.
    
    Provides business logic for creating, updating, and managing talent profiles
    including contract type handling and validation.
    """

    def __init__(self):
        """Initialize the TalentService with the Talent model."""
        super().__init__(Talent)

    def create_talent(self, db: Session, data: TalentIn) -> TalentOut:
        """
        Create a new talent record with validation.

        Args:
            db: Database session for performing operations.
            data: Talent input data containing profile information.

        Returns:
            TalentOut: Created talent record with all fields.

        Raises:
            HTTPException: 400 if validation fails (duplicate email, invalid dates, etc.).
        """
        talent = db.query(Talent).filter(Talent.email == data.email).first()
        validate_talent_create(data=data, talent=talent)

        contract_hours = set_contract_hours(data.contract_type)
        
        created_talents: Talent = self.create(db=db, obj_in=data)
        created_talents.hours = contract_hours

        db.add(created_talents)
        db.commit()
        db.refresh(created_talents)

        return TalentOut.model_validate(created_talents)

    
    def update_talent(self, db: Session, talent_id: int, data: TalentUpdate) -> TalentOut:
        """
        Update an existing talent record.

        Handles special cases like deactivation (sets end_date) and contract type changes
        (updates hours automatically).

        Args:
            db: Database session for performing operations.
            talent_id: ID of the talent to update.
            data: Partial talent data to update.

        Returns:
            TalentOut: Updated talent record.

        Raises:
            HTTPException: 404 if talent not found, 403 if trying to reactivate.
        """
        talent = db.query(Talent).filter(Talent.id == talent_id).first()
        validate_talent_update(data=data, talent=talent)

        if data.is_active is False:
            talent.end_date = datetime.now().date()
        if data.contract_type:
            talent.hours = set_contract_hours(data.contract_type)
        updated_talent = self.update(db, talent, data)

        return TalentOut.model_validate(updated_talent)
    


def get_all_talents(
    db: Session,
    name: str | None = None,
    tal_role: str | None = None,
    contract_type: str | None = None,
    is_active: bool | None = None
) -> List[TalentOut]:
    """
    Retrieve all talents with optional filtering.

    Args:
        db: Database session for querying.
        name: Optional filter by first or last name (partial match).
        tal_role: Optional filter by role.
        contract_type: Optional filter by contract type.
        is_active: Optional filter by active status.

    Returns:
        List of TalentOut objects matching the filters.

    Raises:
        HTTPException: 404 if no talents found.
    """
    query = db.query(Talent)
    talent_exists(query)
    talents = search_filters(
        query=query,
        name=name,
        tal_role=tal_role,
        contract_type=contract_type,
        is_active=is_active
    )
    talent_exists(talents)
    return [TalentOut.model_validate(talent) for talent in talents]
        
    
def get_talent(db: Session, id: int) -> TalentOut:
    """
    Retrieve a single talent by ID.

    Args:
        db: Database session for querying.
        id: Talent ID to retrieve.

    Returns:
        TalentOut object with talent data.

    Raises:
        HTTPException: 404 if talent not found.
    """
    talent = db.query(Talent).filter(Talent.id == id).first()
    talent_exists(talent)
    return TalentOut.model_validate(talent)


     
        
            
        

        
    