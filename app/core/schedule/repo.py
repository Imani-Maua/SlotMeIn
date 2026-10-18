from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.database.models import Schedule, ScheduledShift
from app.core.schedule.schema import AssignmentIn, AssignmentUpdate, ScheduleCreate
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.shifts.schema import shiftSpecification


class ScheduleRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_all(self) -> list[Schedule]:
        return self.db.query(Schedule).order_by(Schedule.week_start.desc()).all()

    def get_by_id(self, schedule_id: int) -> Schedule | None:
        return self.db.query(Schedule).filter(Schedule.id == schedule_id).first()

    def create(self, data: ScheduleCreate) -> Schedule:
        existing = self.db.query(Schedule).filter(
            Schedule.week_start == data.week_start,
            Schedule.status == data.status,
        ).first()
        if existing:
            raise ValueError(
                f"A {data.status} schedule for the week starting {data.week_start} "
                f"already exists (ID {existing.id})."
            )

        saved = Schedule(week_start=data.week_start, week_end=data.week_end, status=data.status)
        self.db.add(saved)
        self.db.flush()

        for entry in data.assignments:
            start_dt = datetime.combine(entry.date_of, entry.start_time)
            end_dt   = datetime.combine(entry.date_of, entry.end_time)
            self.db.add(ScheduledShift(
                talent_id=entry.talent_id,
                date_of=entry.date_of,
                start_time=entry.start_time,
                end_time=entry.end_time,
                shift_hours=(end_dt - start_dt).total_seconds() / 3600,
                shift_name=entry.shift_name,
                schedule_id=saved.id,
            ))

        self.db.commit()
        self.db.refresh(saved)
        return saved

    def update_status(self, schedule_id: int, new_status: str) -> Schedule:
        saved = self.get_by_id(schedule_id)
        if not saved:
            raise LookupError(f"Schedule {schedule_id} not found.")

        if new_status == "draft" and saved.status == "final":
            raise ValueError("Cannot demote a published final schedule back to draft.")

        if new_status == "final" and saved.status != "final":
            conflict = self.db.query(Schedule).filter(
                Schedule.week_start == saved.week_start,
                Schedule.status == "final",
                Schedule.id != schedule_id,
            ).first()
            if conflict:
                raise ValueError(
                    f"A final schedule for this week already exists (ID {conflict.id})."
                )

        saved.status = new_status
        self.db.commit()
        self.db.refresh(saved)
        return saved

    def delete(self, schedule_id: int) -> None:
        saved = self.get_by_id(schedule_id)
        if not saved:
            raise LookupError(f"Schedule {schedule_id} not found.")
        self.db.query(ScheduledShift).filter(ScheduledShift.schedule_id == schedule_id).delete()
        self.db.delete(saved)
        self.db.commit()


    def create_assignment(self, data: AssignmentIn) -> ScheduledShift:
        start_dt = datetime.combine(data.date_of, data.start_time)
        end_dt   = datetime.combine(data.date_of, data.end_time)
        shift = ScheduledShift(
            talent_id=data.talent_id,
            date_of=data.date_of,
            start_time=data.start_time,
            end_time=data.end_time,
            shift_hours=(end_dt - start_dt).total_seconds() / 3600,
            shift_name=data.shift_name,
            schedule_id=data.schedule_id,
        )
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def update_assignment(self, assignment_id: int, data: AssignmentUpdate) -> ScheduledShift:
        shift = self.db.query(ScheduledShift).filter(ScheduledShift.id == assignment_id).first()
        if not shift:
            raise LookupError(f"Assignment {assignment_id} not found.")
        if data.start_time is not None:
            shift.start_time = data.start_time
        if data.end_time is not None:
            shift.end_time = data.end_time
        if data.shift_name is not None:
            shift.shift_name = data.shift_name
        self.db.commit()
        self.db.refresh(shift)
        return shift

    def delete_assignment(self, assignment_id: int) -> None:
        shift = self.db.query(ScheduledShift).filter(ScheduledShift.id == assignment_id).first()
        if not shift:
            raise LookupError(f"Assignment {assignment_id} not found.")
        self.db.delete(shift)
        self.db.commit()

    def get_assignments_for_schedule(self, schedule_id: int) -> list[ScheduledShift]:
        return (
            self.db.query(ScheduledShift)
            .filter(ScheduledShift.schedule_id == schedule_id)
            .all()
        )


    def load_history(self, week_start: date) -> list[assignment]:
        rows = (
            self.db.query(ScheduledShift)
            .filter(
                ScheduledShift.date_of >= week_start - timedelta(days=7),
                ScheduledShift.date_of < week_start,
            )
            .all()
        )
        return [
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
                ),
            )
            for row in rows
            if row.talent_id and row.date_of and row.start_time and row.end_time
        ]
