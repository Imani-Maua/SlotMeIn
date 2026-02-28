"""
API routes for schedule generation and management.
"""

from fastapi import APIRouter, Body, Depends, status, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated, List

from app.database.session import session
from app.database.auth import User
from app.core.schedule.schema import (
    inputDate, ScheduleOut, AssignmentOut, AssignmentUpdate,
    AssignmentIn, ScheduleCreate, StatusUpdate, ValidationRequest
)
from app.core.schedule.shifts.service import ShiftSlotBuilder
from app.core.schedule.talents.repo import TalentRepository
from app.core.schedule.talents.preprocessor import TalentPreprocessor
from app.core.schedule.talents.assembler import TalentAssembler
from app.core.schedule.talents.service import TalentService
from app.core.schedule.allocator.engine.generators import TalentByRole
from app.core.schedule.allocator.service import ScheduleBuilder, UnderstaffedShifts
from app.core.schedule.allocator.entities import weekRange, assignment
from app.core.schedule.shifts.schema import shiftSpecification
from app.authentication.utils.auth_utils import get_current_user
from app.database.models import ScheduledShift, Schedule
from app.core.schedule.allocator.engine.validators import (
        maxHoursValidator, consecutiveValidator, restValidator,
        dailyAssignmentValidator, context,
    )


schedule = APIRouter(tags=["Schedule"])


# GENERATE  (preview only — does NOT save to the database)

@schedule.post("/generate")
async def generate_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    start_date: Annotated[inputDate, Body()]
):
    """
    Run the scheduling algorithm and return a preview.
    Nothing is written to the database — the manager reviews the draft
    and either saves it as a draft or publishes it via POST /commit.
    """

    week_provider = weekRange(start_date=start_date.start_date)

    slots_builder = ShiftSlotBuilder(db=db, start_date=week_provider.get_week()[0])
    assignable_shifts = slots_builder.build_week_slots()

    repo = TalentRepository(session=db)
    preprocessor = TalentPreprocessor(week_provider=week_provider)
    assembler = TalentAssembler(week_provider=week_provider)
    talent_service = TalentService(repo=repo, preprocessor=preprocessor, assembler=assembler)
    talent_objects = talent_service.load_talent_objects()

    talents_by_role = TalentByRole.group_talents(talents=talent_objects)

    week_start = week_provider.get_week()[0]
    week_end   = week_provider.get_week()[-1]

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
                role_count=1,
            )
        )
        for row in history_rows
        if row.talent_id and row.date_of and row.start_time and row.end_time
    ]

    scheduler = ScheduleBuilder(
        availability=talent_objects,
        assignable_shifts=assignable_shifts,
        talents_to_assign=talents_by_role,
        history=history,
    )
    plan = scheduler.generate_schedule()

    understaffed = UnderstaffedShifts(
        conn=db,
        assignable_shifts=assignable_shifts,
        assigned_shifts=plan,
    )
    understaffed_shifts = understaffed.get_all()

    # Return preview data in the shape DraftScheduleGrid expects
    return {
        "week_start": str(week_start),
        "week_end":   str(week_end),
        "assignments": [
            {
                "id":         f"preview-{i}",
                "talent_id":  a.talent_id,
                "tal_role":   a.shift.role_name,
                "shift_name": a.shift.shift_name,
                "date_of":    str(a.shift.start_time.date()),
                "start_time": str(a.shift.start_time.time()),
                "end_time":   str(a.shift.end_time.time()),
            }
            for i, a in enumerate(plan)
        ],
        "understaffed": [
            {
                "shift_name": u.shift_name,
                "role":       u.role_name,
                "required":   u.required,
                "assigned":   u.assigned,
            }
            for u in understaffed_shifts
        ],
    }


def _serialize_schedule(schedule):
    """Map a Schedule ORM object to the dict shape ScheduleOut expects."""
    return {
        "id":         schedule.id,
        "week_start": schedule.week_start,
        "week_end":   schedule.week_end,
        "status":     schedule.status,
        "assignments": [
            {
                "id":          s.id,
                "talent_id":   s.talent_id,
                "date_of":     s.date_of,
                "start_time":  s.start_time,
                "end_time":    s.end_time,
                "shift_name":  s.shift_name,
                "shift_hours": float(s.shift_hours) if s.shift_hours else None,
                "schedule_id": s.schedule_id,
            }
            for s in (schedule.scheduled_shifts or [])
        ],
    }



# LIST ALL SCHEDULES

@schedule.get("/", response_model=List[ScheduleOut])
async def list_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
):
    """Return all schedules ordered by week_start descending."""
    schedules = db.query(Schedule).order_by(Schedule.week_start.desc()).all()
    return [_serialize_schedule(s) for s in schedules]



# COMMIT  (save preview to DB as draft or final)


@schedule.post("/commit", response_model=ScheduleOut)
async def commit_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: ScheduleCreate,
):
    """
    Persist a previewed schedule to the database.
    status='draft'  → saves a work-in-progress (editable later).
    status='final'  → publishes the schedule (blocked if a final/draft
                       already exists for the same week).
    """

    # Block duplicate schedules for the same week
    existing = db.query(Schedule).filter(
        Schedule.week_start == data.week_start,
        Schedule.status == data.status,
    ).first()
    if existing:
        label = "final" if data.status == "final" else "draft"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {label} schedule for the week starting {data.week_start} already exists (ID {existing.id}).",
        )

    saved = Schedule(week_start=data.week_start, week_end=data.week_end, status=data.status)
    db.add(saved)
    db.flush()

    for entry in data.assignments:
        start_dt = datetime.combine(entry.date_of, entry.start_time)
        end_dt   = datetime.combine(entry.date_of, entry.end_time)
        shift_hours = (end_dt - start_dt).total_seconds() / 3600
        db.add(ScheduledShift(
            talent_id=entry.talent_id,
            date_of=entry.date_of,
            start_time=entry.start_time,
            end_time=entry.end_time,
            shift_hours=shift_hours,
            shift_name=entry.shift_name,
            schedule_id=saved.id,
        ))

    db.commit()
    db.refresh(saved)
    return saved



# GET SINGLE SCHEDULE


@schedule.get("/{schedule_id}", response_model=ScheduleOut)
async def get_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
):
    saved = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _serialize_schedule(saved)



# PATCH STATUS  (promote draft → final, or any status change)


@schedule.patch("/{schedule_id}/status", response_model=ScheduleOut)
async def update_schedule_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
    data: StatusUpdate,
):

    saved = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if data.status == "draft" and saved.status == "final":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot demote a published final schedule back to draft. Delete and re-create it instead.",
        )

    if data.status == "final" and saved.status != "final":
        existing = db.query(Schedule).filter(
            Schedule.week_start == saved.week_start,
            Schedule.status == "final",
            Schedule.id != schedule_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A final schedule for this week already exists (ID {existing.id}).",
            )

    saved.status = data.status
    db.commit()
    db.refresh(saved)
    return _serialize_schedule(saved)



# DELETE SCHEDULE


@schedule.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
):
    saved = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.query(ScheduledShift).filter(ScheduledShift.schedule_id == schedule_id).delete()
    db.delete(saved)
    db.commit()



# ASSIGNMENT CRUD


@schedule.post("/assignments/", response_model=AssignmentOut)
async def create_assignment(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: AssignmentIn,
):
    
    start_dt = datetime.combine(data.date_of, data.start_time)
    end_dt   = datetime.combine(data.date_of, data.end_time)
    shift_hours = (end_dt - start_dt).total_seconds() / 3600
    new_shift = ScheduledShift(
        talent_id=data.talent_id,
        date_of=data.date_of,
        start_time=data.start_time,
        end_time=data.end_time,
        shift_hours=shift_hours,
        shift_name=data.shift_name,
        schedule_id=data.schedule_id,
    )
    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)
    return new_shift


@schedule.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    assignment_id: int,
    data: AssignmentUpdate,
):
    shift = db.query(ScheduledShift).filter(ScheduledShift.id == assignment_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if data.start_time is not None:
        shift.start_time = data.start_time
    if data.end_time is not None:
        shift.end_time = data.end_time
    if data.shift_name is not None:
        shift.shift_name = data.shift_name
    db.commit()
    db.refresh(shift)
    return shift


@schedule.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    assignment_id: int,
):
    from app.database.models import ScheduledShift
    shift = db.query(ScheduledShift).filter(ScheduledShift.id == assignment_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(shift)
    db.commit()


# VALIDATE ASSIGNMENT  (constraint check, non-blocking, informational)


@schedule.post("/validate_assignment")
async def validate_assignment(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: ValidationRequest,
):
    """
    Run all scheduling validators against a proposed manual assignment.
    Returns a list of human-readable violation messages.
    An empty list means no violations. Violations are informational — the
    manager can always override.
    """
   

    shift_date = data.date_of
    week_start = shift_date - timedelta(days=shift_date.weekday())
    week_provider = weekRange(start_date=week_start)
    repo = TalentRepository(session=db)
    preprocessor = TalentPreprocessor(week_provider=week_provider)
    assembler = TalentAssembler(week_provider=week_provider)
    talent_objects = TalentService(
        repo=repo, preprocessor=preprocessor, assembler=assembler
    ).load_talent_objects()

    if data.talent_id not in talent_objects:
        raise HTTPException(status_code=404, detail="Talent not found or inactive")

    proposed_shift = shiftSpecification(
        template_id=None,
        start_time=datetime.combine(data.date_of, data.start_time),
        end_time=datetime.combine(data.date_of, data.end_time),
        shift_name=data.shift_name or "",
        role_name="",
        role_count=1,
    )

    existing_shifts = (
        db.query(ScheduledShift)
        .filter(ScheduledShift.schedule_id == data.schedule_id)
        .all()
    ) if data.schedule_id else []

    existing_assignments = [
        assignment(
            talent_id=s.talent_id,
            shift_id=s.id,
            shift=shiftSpecification(
                template_id=None,
                start_time=datetime.combine(s.date_of, s.start_time),
                end_time=datetime.combine(s.date_of, s.end_time),
                shift_name=s.shift_name or "",
                role_name="",
                role_count=1,
            ),
        )
        for s in existing_shifts
        if s.talent_id and s.start_time and s.end_time
    ]

    ctx = context.contextFinder(
        data.talent_id, proposed_shift, talent_objects, existing_assignments
    )

    violations = []

    if not maxHoursValidator().can_assign_shift(ctx):
        avail = talent_objects[data.talent_id]
        violations.append(
            f"Exceeds weekly hours — would exceed their {avail.weeklyhours}h contract limit."
        )

    if not dailyAssignmentValidator().can_assign_shift(ctx):
        violations.append(
            f"Already scheduled — already has a shift on {data.date_of.strftime('%A %d %b')}."
        )

    if not restValidator().can_assign_shift(ctx):
        violations.append("Insufficient rest — less than 11 hours since their previous shift.")

    if not consecutiveValidator().can_assign_shift(ctx):
        violations.append("Too many consecutive days — this would be their 7th consecutive working day.")

    return {"violations": violations}
