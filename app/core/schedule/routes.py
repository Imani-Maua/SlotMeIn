import asyncio
import json
from fastapi import APIRouter, Body, Depends, status, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, List

from app.database.session import session
from app.database.auth import User
from app.core.schedule.schema import (
    inputDate, ScheduleOut, AssignmentOut, AssignmentUpdate,
    AssignmentIn, ScheduleCreate, StatusUpdate,
)
from app.core.schedule.repo import ScheduleRepository
from app.database.models import Schedule
from app.authentication.utils.auth_utils import get_current_user
from app.redis.client import get_redis
from app.core.schedule.events import ScheduleJobQueue, ScheduleEvent
from app.redis.result_store import JobResultStore
import redis


schedule = APIRouter(tags=["Schedule"])


def _serialize_schedule(schedule: Schedule):
    return {
        "id":         schedule.id,
        "week_start": schedule.week_start,
        "week_end":   schedule.week_end,
        "status":     schedule.status,
        "assignments": [
            {
                "id":          assignment.id,
                "talent_id":   assignment.talent_id,
                "date_of":     assignment.date_of,
                "start_time":  assignment.start_time,
                "end_time":    assignment.end_time,
                "shift_name":  assignment.shift_name,
                "shift_hours": float(assignment.shift_hours) if assignment.shift_hours else None,
                "schedule_id": assignment.schedule_id,
            }
            for assignment in (schedule.scheduled_shifts or [])
        ],
    }



@schedule.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_schedule(
    _: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[inputDate, Body()],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
):
    queue = ScheduleJobQueue(redis_client)
    store = JobResultStore(redis_client)

    job_id = queue.publish(str(start_date.start_date))
    store.set_pending(job_id)

    return {"job_id": job_id, "status": "pending"}


@schedule.get("/jobs/{job_id}")
async def get_job_result(
    _: Annotated[User, Depends(get_current_user)],
    job_id: str,
    redisclient: Annotated[redis.Redis, Depends(get_redis)],
):
    result = JobResultStore(redisclient).get(job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired.",
        )
    return result


@schedule.get("/events/{job_id}")
async def stream_job_events(
    _: Annotated[User, Depends(get_current_user)],
    job_id: str,
    request: Request,
    redisclient: Annotated[redis.Redis, Depends(get_redis)],
):
    from app.redis.event_publisher import EventPublisher
    terminal_events = {ScheduleEvent.JOB_DONE, ScheduleEvent.JOB_FAILED}
    publisher = EventPublisher(redisclient)

    async def event_stream():
        last_id = "0"
        while True:
            if await request.is_disconnected():
                break
            messages = await asyncio.to_thread(publisher.read, last_id)
            for msg_id, fields in messages:
                last_id = msg_id
                payload = json.loads(fields["payload"])
                if payload.get("job_id") != job_id:
                    continue
                yield f"event: {fields['event']}\ndata: {fields['payload']}\n\n"
                if fields["event"] in terminal_events:
                    return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@schedule.get("/", response_model=List[ScheduleOut])
async def list_schedules(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
):
    return [_serialize_schedule(schedule) for schedule in ScheduleRepository(db).get_all()]


@schedule.get("/{schedule_id}", response_model=ScheduleOut)
async def get_schedule(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
):
    schedule = ScheduleRepository(db).get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return _serialize_schedule(schedule)


@schedule.post("/commit", response_model=ScheduleOut)
async def commit_schedule(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: ScheduleCreate,
):
    try:
        return _serialize_schedule(ScheduleRepository(db).create(data))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@schedule.patch("/{schedule_id}/status", response_model=ScheduleOut)
async def update_schedule_status(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
    data: StatusUpdate,
):
    try:
        return _serialize_schedule(ScheduleRepository(db).update_status(schedule_id, data.status))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@schedule.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    schedule_id: int,
):
    try:
        ScheduleRepository(db).delete(schedule_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



@schedule.post("/assignments/", response_model=AssignmentOut)
async def create_assignment(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    data: AssignmentIn,
):
    return ScheduleRepository(db).create_assignment(data)


@schedule.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    assignment_id: int,
    data: AssignmentUpdate,
):
    try:
        return ScheduleRepository(db).update_assignment(assignment_id, data)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@schedule.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(session)],
    assignment_id: int,
):
    try:
        ScheduleRepository(db).delete_assignment(assignment_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


