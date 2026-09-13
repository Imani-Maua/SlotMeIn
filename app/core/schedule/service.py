from datetime import date
from sqlalchemy.orm import Session
import structlog

from app.core.schedule.repo import ScheduleRepository
from app.core.schedule.allocator.entities import weekRange
from app.core.schedule.allocator.service import CSPScheduler, UnderstaffedShifts
from app.core.schedule.shifts.service import ShiftSlotBuilder
from app.core.schedule.talents.repo import TalentRepository
from app.core.schedule.talents.preprocessor import TalentPreprocessor
from app.core.schedule.talents.assembler import TalentAssembler
from app.core.schedule.talents.service import TalentService

log = structlog.get_logger()


class SchedulingService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ScheduleRepository(db)

    def _load_talents(self, week_provider: weekRange):
        return TalentService(
            repo=TalentRepository(session=self.db),
            preprocessor=TalentPreprocessor(week_provider=week_provider),
            assembler=TalentAssembler(week_provider=week_provider),
        ).load_talent_objects()

    def generate(self, start_date: date) -> dict:
        week_provider = weekRange(start_date=start_date)
        week = week_provider.get_week()

        assignable_shifts = ShiftSlotBuilder(
            db=self.db, start_date=week[0]
        ).build_week_slots()
        log.info("schedule_generation: shift_slots_built", week_start=str(week[0]), count=len(assignable_shifts))

        talent_objects = self._load_talents(week_provider)
        log.info("schedule_generation: talents_loaded", count=len(talent_objects))

        history = self.repo.load_history(week[0])
        log.info("schedule_generation: history_loaded", count=len(history))

        plan = CSPScheduler(
            availability=talent_objects,
            assignable_shifts=assignable_shifts,
            talents_to_assign=None,
            history=history,
        ).generate_schedule()
        log.info("schedule_generation: schedule_generated", assignments=len(plan))

        understaffed = UnderstaffedShifts(
            assignable_shifts=assignable_shifts,
            assigned_shifts=plan,
        ).get_all()
        log.info("schedule_generation: understaffed_computed", count=len(understaffed))

        return {
            "week_start":   str(week[0]),
            "week_end":     str(week[-1]),
            "assignments": [
                {
                    "id":         f"preview-{i}",
                    "talent_id":  assignment.talent_id,
                    "tal_role":   assignment.shift.role_name,
                    "shift_name": assignment.shift.shift_name,
                    "date_of":    str(assignment.shift.start_time.date()),
                    "start_time": str(assignment.shift.start_time.time()),
                    "end_time":   str(assignment.shift.end_time.time()),
                }
                for i, assignment in enumerate(plan)
            ],
            "understaffed": understaffed,
        }

