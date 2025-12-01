"""
API routes for schedule generation.

This module provides the main endpoint for generating optimized work schedules
based on shift requirements, talent availability, and constraints.
"""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import Annotated

from app.database.session import session
from app.database.auth import User
from app.core.schedule.schema import inputDate
from app.core.schedule.shifts.service import ShiftSlotBuilder
from app.core.schedule.talents.repo import TalentRepository
from app.core.schedule.talents.preprocessor import TalentPreprocessor
from app.core.schedule.talents.assembler import TalentAssembler
from app.core.schedule.talents.service import TalentService
from app.core.schedule.allocator.allocator.engine.generators import TalentByRole
from app.core.schedule.allocator.allocator.service import ScheduleBuilder, UnderstaffedShifts
from app.core.schedule.allocator.entities import weekRange
from app.authentication.utils.auth_utils import get_current_user
from datetime import timedelta



schedule = APIRouter(tags=["Schedule"])


@schedule.post("/generate")
async def generate_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    start_date: Annotated[inputDate, Body()]
):
    """
    Generate an optimized work schedule for a week.

    Requires authentication. This is the main scheduling algorithm that:
    1. Builds shift slots for the week based on templates
    2. Loads talent availability and constraints
    3. Groups talents by role
    4. Runs the optimization algorithm to assign talents to shifts
    5. Identifies any understaffed shifts

    The algorithm attempts to:
    - Respect talent constraints (unavailability, preferences)
    - Meet shift staffing requirements
    - Balance workload across talents
    - Respect contract hour limits

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        start_date: Input containing the start date for the schedule week.

    Returns:
        dict: Schedule result containing:
            - assignments: List of talent-to-shift assignments with details
            - understaffed: List of shifts that couldn't be fully staffed

    Raises:
        HTTPException: 403 if shift period or templates are invalid.
    """
    # 1. Get all the dates to schedule
    week_provider = weekRange(start_date=start_date.start_date)

    # 2. Build the shift slots
    slots_builder = ShiftSlotBuilder(db=db, start_date=week_provider.get_week()[0])
    assignable_shifts = slots_builder.build_week_slots()

    # 3. Build talent availability
    repo = TalentRepository(session=db)
    preprocessor = TalentPreprocessor(week_provider=week_provider)
    assembler = TalentAssembler(week_provider=week_provider)
    talent_service = TalentService(repo=repo, preprocessor=preprocessor, assembler=assembler)
    talent_objects = talent_service.load_talent_objects()

    # 4. Group talents by role
    talents_by_role = TalentByRole.group_talents(talents=talent_objects)

    # 5. Run the scheduler
    scheduler = ScheduleBuilder(
        availability=talent_objects, 
        assignable_shifts=assignable_shifts, 
        talents_to_assign=talents_by_role
    )
    plan = scheduler.generate_schedule()

    understaffed = UnderstaffedShifts(
        conn=db,
        assignable_shifts=assignable_shifts,
        assigned_shifts=plan
    )
    understaffed_shifts = understaffed.get_all()

    return {
        "assignments": [
            {
                "talent_id": a.talent_id,
                "shift_id": a.shift_id,
                "role": a.shift.role_name,
                "shift_name": a.shift.shift_name,
                "start": a.shift.start_time,
                "end": a.shift.end_time
            } for a in plan
        ],
        "understaffed": [
            {
                "shift_id": u.shift_id,
                "shift_name": u.shift_name,
                "role": u.role_name,
                "required": u.required,
                "assigned": u.assigned,
                "missing": u.missing,
                "start": u.shift_start,
                "end": u.shift_end
            } for u in understaffed_shifts
        ]
    }










