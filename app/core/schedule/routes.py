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
from app.core.schedule.allocator.engine.generators import TalentByRole
from app.core.schedule.allocator.service import ScheduleBuilder, UnderstaffedShifts
from app.core.schedule.allocator.entities import weekRange
from app.authentication.utils.auth_utils import get_current_user
from datetime import timedelta
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.shifts.schema import shiftSpecification
from datetime import datetime


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
    6. Persists the schedule and all assignments to the database

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
            - schedule_id: ID of the saved schedule record
            - assignments: List of talent-to-shift assignments with details
            - understaffed: List of shifts that couldn't be fully staffed

    Raises:
        HTTPException: 403 if shift period or templates are invalid.
    """
    from app.database.models import Schedule, ScheduledShift

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

    # 4.5 Load recent shift history for continuity (previous 7 days)
    week_start = week_provider.get_week()[0]
    history_rows = (
        db.query(ScheduledShift)
        .filter(
            ScheduledShift.date_of >= week_start - timedelta(days=7),
            ScheduledShift.date_of < week_start,
        )
        .all()
    )

    history = [
        assignment(
            talent_id=row.talent_id,
            shift_id=row.id,
            shift=shiftSpecification(
                template_id=None,
                start_time=datetime.combine(row.date_of, row.start_time),
                end_time=datetime.combine(row.date_of, row.end_time),
                shift_name="",
                role_name="",
                role_count=1
            )
        )
        for row in history_rows
        if row.talent_id and row.date_of and row.start_time and row.end_time
    ]

    # 5. Run the scheduler
    scheduler = ScheduleBuilder(
        availability=talent_objects, 
        assignable_shifts=assignable_shifts, 
        talents_to_assign=talents_by_role,
        history=history
    )
    plan = scheduler.generate_schedule()

    # 6. Identify understaffed shifts
    understaffed = UnderstaffedShifts(
        conn=db,
        assignable_shifts=assignable_shifts,
        assigned_shifts=plan
    )
    understaffed_shifts = understaffed.get_all()

    # 7. Persist the schedule and all assignments to the database
    week_end = week_provider.get_week()[-1]

    saved_schedule = Schedule(
        week_start=week_start,
        week_end=week_end,
        status="draft"
    )
    db.add(saved_schedule)
    db.flush()  # get the ID before committing

    for assignment in plan:
        shift_hours = (assignment.shift.end_time - assignment.shift.start_time).total_seconds() / 3600
        db.add(ScheduledShift(
            talent_id=assignment.talent_id,
            date_of=assignment.shift.start_time.date(),
            start_time=assignment.shift.start_time.time(),
            end_time=assignment.shift.end_time.time(),
            shift_hours=shift_hours,
            schedule_id=saved_schedule.id
        ))

    db.commit()

    return {
        "schedule_id": saved_schedule.id,
        "assignments": [
            {
                "talent_id": assignment.talent_id,
                "shift_id": assignment.shift_id,
                "role": assignment.shift.role_name,
                "shift_name": assignment.shift.shift_name,
                "start": assignment.shift.start_time,
                "end": assignment.shift.end_time
            } for assignment in plan
        ],
        "understaffed": [
            {
                "shift_id": understaffed_shift.shift_id,
                "shift_name": understaffed_shift.shift_name,
                "role": understaffed_shift.role_name,
                "required": understaffed_shift.required,
                "assigned": understaffed_shift.assigned,
                "missing": understaffed_shift.missing,
                "start": understaffed_shift.shift_start,
                "end": understaffed_shift.shift_end
            } for understaffed_shift in understaffed_shifts
        ]
    }


@schedule.get("/{schedule_id}")
async def get_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int
):
    """
    Retrieve a previously generated schedule by its ID.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.
        schedule_id: ID of the schedule to retrieve.

    Returns:
        dict: The schedule metadata and all its shift assignments.

    Raises:
        HTTPException: 404 if the schedule does not exist.
    """
    from app.database.models import Schedule, ScheduledShift
    from fastapi import HTTPException

    saved_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not saved_schedule:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    shifts = (
        db.query(ScheduledShift)
        .filter(ScheduledShift.schedule_id == schedule_id)
        .all()
    )

    return {
        "schedule_id": saved_schedule.id,
        "week_start": saved_schedule.week_start,
        "week_end": saved_schedule.week_end,
        "status": saved_schedule.status,
        "assignments": [
            {
                "talent_id": shift.talent_id,
                "date": shift.date_of,
                "start": shift.start_time,
                "end": shift.end_time,
                "shift_hours": float(shift.shift_hours) if shift.shift_hours else None
            }
            for shift in shifts
        ]
    }
