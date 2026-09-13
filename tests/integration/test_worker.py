"""
End-to-end tests for the worker pipeline.

Uses a real Redis connection but mocks SchedulingService so no DB data is needed.
Tests the full flow: publish → consume → process → result stored in Redis.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.redis.client import create_redis_client as get_redis
from app.redis.job_queue import JobQueue
from app.core.schedule.events import ScheduleJobQueue
from app.redis.result_store import JobResultStore
from app.redis.event_publisher import EventPublisher
from app.core.schedule.worker import process_job


FAKE_RESULT = {
    "week_start": "2026-09-14",
    "week_end":   "2026-09-20",
    "assignments": [
        {"id": "preview-0", "talent_id": 1, "shift_name": "am", "date_of": "2026-09-14"}
    ],
    "understaffed": [],
}


@pytest.fixture
def redis_client():
    return get_redis()


@pytest.fixture
def queue(redis_client):
    q = ScheduleJobQueue(redis_client)
    q.create_consumer_group()
    # Advance the group pointer to now so stale messages from previous runs are skipped
    redis_client.xgroup_setid(ScheduleJobQueue.STREAM, ScheduleJobQueue.GROUP, "$")
    return q


@pytest.fixture
def store(redis_client):
    return JobResultStore(redis_client)


@pytest.fixture
def publisher(redis_client):
    return EventPublisher(redis_client)


# ── process_job unit tests ─────────────────────────────────────────────────

@patch("app.core.schedule.worker.SessionLocal")
@patch("app.core.schedule.worker.SchedulingService")
def test_process_job_stores_done_on_success(mock_service, mock_session):
    mock_service.return_value.generate.return_value = FAKE_RESULT

    r = get_redis()
    store = JobResultStore(r)
    pub = EventPublisher(r)
    job_id = "test-success-job"
    store.set_pending(job_id)

    process_job(job_id, "2026-09-14", store, pub)

    result = store.get(job_id)
    assert result["status"] == "done"
    assert result["result"]["week_start"] == "2026-09-14"
    assert len(result["result"]["assignments"]) == 1


@patch("app.core.schedule.worker.SessionLocal")
@patch("app.core.schedule.worker.SchedulingService")
def test_process_job_stores_failed_on_error(mock_service, mock_session):
    mock_service.return_value.generate.side_effect = RuntimeError("something broke")

    r = get_redis()
    store = JobResultStore(r)
    pub = EventPublisher(r)
    job_id = "test-failed-job"
    store.set_pending(job_id)

    process_job(job_id, "2026-09-14", store, pub)

    result = store.get(job_id)
    assert result["status"] == "failed"
    assert "something broke" in result["error"]


@patch("app.core.schedule.worker.SessionLocal")
@patch("app.core.schedule.worker.SchedulingService")
def test_process_job_transitions_through_running(mock_service, mock_session):
    """Status must be 'running' while the job is being processed."""
    r = get_redis()
    store = JobResultStore(r)
    pub = EventPublisher(r)
    job_id = "test-running-job"
    store.set_pending(job_id)

    observed_status = []

    def fake_generate(_):
        observed_status.append(store.get(job_id)["status"])
        return FAKE_RESULT

    mock_service.return_value.generate.side_effect = fake_generate

    process_job(job_id, "2026-09-14", store, pub)

    assert observed_status == ["running"]
    assert store.get(job_id)["status"] == "done"


# ── DLQ ───────────────────────────────────────────────────────────────────

def test_recover_moves_exhausted_messages_to_dlq(redis_client, queue):
    """
    Messages that have been delivered more than MAX_RETRIES times
    must be moved to the DLQ and acked off the main stream.
    """
    # Publish a job and deliver it MAX_RETRIES + 1 times without acking
    job_id = queue.publish("2026-09-14")
    for _ in range(JobQueue.MAX_RETRIES + 1):
        list(queue.consume_msgs("dlq-test-consumer", block_ms=1000))

    dlq_key = f"{ScheduleJobQueue.STREAM}:dlq"
    dlq_before = redis_client.xlen(dlq_key)

    # recover() should detect the over-limit message and move it to the DLQ
    list(queue.recover_orphaned_msgs("dlq-test-consumer"))

    assert redis_client.xlen(dlq_key) == dlq_before + 1

    # The original stream should no longer have it pending
    pending = redis_client.xpending_range(
        ScheduleJobQueue.STREAM, ScheduleJobQueue.GROUP, "-", "+", count=10,
        consumername="dlq-test-consumer",
    )
    assert all(p["message_id"] != job_id for p in pending)


# ── Full round-trip ────────────────────────────────────────────────────────

@patch("app.core.schedule.worker.SessionLocal")
@patch("app.core.schedule.worker.SchedulingService")
def test_full_stream_round_trip(mock_service, mock_session, queue, store, publisher):
    """
    Simulates the complete flow:
      API publishes job → worker consumes from stream → result in Redis.
    """
    mock_service.return_value.generate.return_value = FAKE_RESULT

    # API side: publish job and mark pending
    job_id = queue.publish("2026-09-14")
    store.set_pending(job_id)

    assert store.get(job_id)["status"] == "pending"

    # Worker side: consume one message and process it
    for msg_id, fields in queue.consume_msgs("test-consumer", block_ms=2000):
        process_job(fields["job_id"], fields["start_date"], store, publisher)
        queue.ack(msg_id)
        break

    # Verify result is stored and correct
    result = store.get(job_id)
    assert result["status"] == "done"
    assert result["result"]["week_start"] == "2026-09-14"
    assert result["result"]["understaffed"] == []
