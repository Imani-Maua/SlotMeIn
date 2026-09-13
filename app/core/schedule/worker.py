from datetime import date

import structlog

from app.database.session import SessionLocal
from app.core.schedule.events import ScheduleEvent
from app.redis.result_store import JobResultStore
from app.redis.event_publisher import EventPublisher
from app.core.schedule.service import SchedulingService

log = structlog.get_logger()


def process_job(job_id: str, start_date_str: str, store: JobResultStore, publisher: EventPublisher):
    store.set_running(job_id)
    publisher.publish(ScheduleEvent.JOB_STARTED, {"job_id": job_id, "start_date": start_date_str})
    log.info("csp_scheduler_job_started", job_id=job_id, start_date=start_date_str)

    db = SessionLocal()
    try:
        publisher.publish(ScheduleEvent.SOLVER_RUNNING, {"job_id": job_id})
        log.info("csp_scheduler_solver_running", job_id=job_id)
        result = SchedulingService(db).generate(date.fromisoformat(start_date_str))
        store.set_done(job_id, result)
        publisher.publish(ScheduleEvent.JOB_DONE, {
            "job_id": job_id,
            "assignments": len(result.get("assignments", [])),
            "understaffed": len(result.get("understaffed", [])),
        })
        log.info("csp_scheduler_job_done", job_id=job_id,
                 assignments=len(result.get("assignments", [])),
                 understaffed=len(result.get("understaffed", [])))
    except Exception as e:
        store.set_failed(job_id, str(e))
        publisher.publish(ScheduleEvent.JOB_FAILED, {"job_id": job_id, "error": str(e)})
        log.error("csp_scheduler_job_failed", job_id=job_id, error=str(e))
    finally:
        db.close()
