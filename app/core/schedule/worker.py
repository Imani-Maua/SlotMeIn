from datetime import date, time, timedelta

import structlog
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.database.session import SessionLocal
from app.database.models import Schedule as ScheduleModel
from app.core.schedule.events import ScheduleEvent
from app.redis.result_store import JobResultStore
from app.redis.event_publisher import EventPublisher
from app.core.schedule.service import SchedulingService
from app.core.schedule.repo import ScheduleRepository
from app.core.schedule.schema import ScheduleCreate, AssignmentBase
from app.core.schedule.config_store import SchedulerConfig
from app.core.schedule.allocator.entities import weekRange


def _user_facing_error(e: Exception) -> str:
    if isinstance(e, (OperationalError, SQLAlchemyError)):
        return "Database error while generating the schedule. Please try again."
    if isinstance(e, ValueError):
        return str(e)  # already clean (e.g. "A draft for this week already exists")
    return "Schedule generation failed. Please try again."

log = structlog.get_logger()


def _build_occupancy_lookup(start_date: date, config: SchedulerConfig) -> dict[str, dict[str, float]]:
    lookup = {}
    for i in range(7):
        dt = start_date + timedelta(days=i)
        weekday_occ = config.occupancy_by_weekday.get(dt.strftime("%A"))
        if weekday_occ is None:
            continue
        shifts = {}
        if weekday_occ.morning is not None:
            shifts["morning"] = weekday_occ.morning
        if weekday_occ.afternoon is not None:
            shifts["afternoon"] = weekday_occ.afternoon
        if shifts:
            lookup[str(dt)] = shifts
    return lookup


def process_job(job_id: str, start_date_str: str, store: JobResultStore, publisher: EventPublisher, config: SchedulerConfig | None = None):
    store.set_running(job_id)
    publisher.publish(ScheduleEvent.JOB_STARTED, {"job_id": job_id, "start_date": start_date_str})
    log.info("csp_scheduler_job_started", job_id=job_id, start_date=start_date_str)

    cfg = config or SchedulerConfig()
    start_date = date.fromisoformat(start_date_str)
    week_start = weekRange(start_date=start_date).get_week()[0]
    daily_occupancy = _build_occupancy_lookup(week_start, cfg) or None

    db = SessionLocal()
    try:
        publisher.publish(ScheduleEvent.SOLVER_RUNNING, {"job_id": job_id})
        log.info("csp_scheduler_solver_running", job_id=job_id)
        result = SchedulingService(db).generate(start_date, daily_occupancy=daily_occupancy, use_weather=cfg.use_weather)
        log.info("csp_scheduler_solved", job_id=job_id, assignments=len(result.get("assignments", [])))

        # Replace any existing draft for this week so re-generating is safe
        week_start = date.fromisoformat(result["week_start"])
        existing_draft = db.query(ScheduleModel).filter(
            ScheduleModel.week_start == week_start,
            ScheduleModel.status == "draft",
        ).first()
        if existing_draft:
            ScheduleRepository(db).delete(existing_draft.id)
            log.info("csp_scheduler_replaced_existing_draft", job_id=job_id, old_id=existing_draft.id)

        saved = ScheduleRepository(db).create(ScheduleCreate(
            week_start=week_start,
            week_end=date.fromisoformat(result["week_end"]),
            status="draft",
            assignments=[
                AssignmentBase(
                    talent_id=a["talent_id"],
                    date_of=date.fromisoformat(a["date_of"]),
                    start_time=time.fromisoformat(a["start_time"]),
                    end_time=time.fromisoformat(a["end_time"]),
                    shift_name=a.get("shift_name"),
                )
                for a in result["assignments"]
            ],
            staffing_requirements=result.get("staffing_requirements", []),
        ))
        log.info("csp_scheduler_draft_saved", job_id=job_id, schedule_id=saved.id)

        store.set_done(job_id, {
            "schedule_id":       saved.id,
            "week_start":        result["week_start"],
            "week_end":          result["week_end"],
            "assignment_count":  len(result["assignments"]),
            "understaffed_count": len(result["understaffed"]),
        })
        publisher.publish(ScheduleEvent.JOB_DONE, {
            "job_id":      job_id,
            "schedule_id": saved.id,
            "assignments": len(result["assignments"]),
            "understaffed": len(result["understaffed"]),
        })
        log.info("csp_scheduler_job_done", job_id=job_id, schedule_id=saved.id,
                 assignments=len(result["assignments"]),
                 understaffed=len(result["understaffed"]))
    except Exception as e:
        msg = _user_facing_error(e)
        store.set_failed(job_id, msg)
        publisher.publish(ScheduleEvent.JOB_FAILED, {"job_id": job_id, "error": msg})
        log.error("csp_scheduler_job_failed", job_id=job_id, error=str(e))
    finally:
        db.close()
