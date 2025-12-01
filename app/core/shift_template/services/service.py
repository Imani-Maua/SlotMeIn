"""
Shift template service layer for managing shift time templates.

This module provides CRUD operations for shift templates, which define the
time ranges for different shift types within a shift period.

Note: Currently allows duplicate/overlapping templates within a period.
This is a known limitation to be addressed in v2.
"""

from sqlalchemy.orm import Session
from datetime import time
from typing import List
from app.core.utils.crud import CRUDBase
from app.database.models import ShiftPeriod, ShiftTemplate
from app.core.shift_template.schema import TemplateIn, TemplateOut, TemplateUpdate
from app.core.shift_template.services.validators import validate_shift_template, validate_shift_template_update, template_exists
from app.core.shift_template.utils import search_filters


class TemplateService(CRUDBase[ShiftTemplate, TemplateIn, TemplateUpdate]):
    """
    Service class for managing shift templates.
    
    Shift templates define the time ranges (start/end times) for different
    shift types within a shift period. They are used as building blocks for
    schedule generation.
    """

    def __init__(self):
        """Initialize the TemplateService with the ShiftTemplate model."""
        super().__init__(ShiftTemplate)
    

    def create_template(self, db: Session, data: TemplateIn) -> TemplateOut:
        """
        Create a new shift template.

        Validates that the template times fall within the associated shift period
        and meet minimum shift length requirements (4 hours).

        Args:
            db: Database session for performing operations.
            data: Template input data including period_id, shift times, and requirements.

        Returns:
            TemplateOut: Created shift template record.

        Raises:
            HTTPException: 400 if validation fails (invalid times, period not found, etc.).
        """
        shift_period = db.query(ShiftPeriod).filter(ShiftPeriod.id == data.period_id).first()
        validate_shift_template(data=data, period=shift_period)
        created_templates = self.create(db=db, obj_in=data)
        return TemplateOut.model_validate(created_templates)
    
    def update_template(self, db: Session, data: TemplateUpdate, template_id: int) -> TemplateOut:
        """
        Update an existing shift template.

        Validates that any time changes still fall within the shift period
        and maintain minimum shift length.

        Args:
            db: Database session for performing operations.
            data: Partial template data to update.
            template_id: ID of the template to update.

        Returns:
            TemplateOut: Updated shift template record.

        Raises:
            HTTPException: 404 if template not found, 400 if validation fails.
        """
        template = db.query(ShiftTemplate).filter(ShiftTemplate.id == template_id).first()
        validate_shift_template_update(data=data, template=template)
        updated_template = self.update(db=db, db_obj=template, obj_in=data)
        return TemplateOut.model_validate(updated_template)
    
    def delete_template(self, db: Session, template_id: int) -> None:
        """
        Delete a shift template.

        Args:
            db: Database session for performing operations.
            template_id: ID of the template to delete.

        Raises:
            HTTPException: 404 if template not found.
        """
        template = db.query(ShiftTemplate).filter(ShiftTemplate.id == template_id).first()
        template_exists(template)
        self.delete(db=db, id=template_id)


def get_template(db: Session, id: int) -> TemplateOut:
    """
    Retrieve a single shift template by ID.

    Args:
        db: Database session for querying.
        id: Template ID to retrieve.

    Returns:
        TemplateOut: Shift template record.

    Raises:
        HTTPException: 404 if template not found.
    """
    template = db.query(ShiftTemplate).filter(ShiftTemplate.id == id).first()
    template_exists(template)
    return TemplateOut.model_validate(template)



def get_all_templates(
    db: Session,
    shift_name: str | None = None,
    shift_start: time | None = None,
    shift_end: time | None = None
) -> List[TemplateOut]:
    """
    Retrieve all shift templates with optional filtering.

    Args:
        db: Database session for querying.
        shift_name: Optional filter by shift period name.
        shift_start: Optional filter by shift start time.
        shift_end: Optional filter by shift end time.

    Returns:
        List of TemplateOut objects matching the filters.

    Raises:
        HTTPException: 404 if no templates found.
    """
    query = db.query(ShiftTemplate).join(ShiftTemplate.period)
    templates = search_filters(
        query=query,
        shift_name=shift_name,
        shift_end=shift_end,
        shift_start=shift_start
    )
    template_exists(templates)
    return [TemplateOut.model_validate(template) for template in templates]
