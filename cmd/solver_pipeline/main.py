import structlog

from app.config.logging import configure_logging
from app.redis.client import create_redis_client
from app.redis.worker import Worker
from app.redis.result_store import JobResultStore
from app.redis.event_publisher import EventPublisher
from app.core.schedule.events import ScheduleJobQueue
from app.core.schedule.worker import process_job

configure_logging()
log = structlog.get_logger()

CONSUMER_NAME = "worker-1"

if __name__ == "__main__":
    redis_client = create_redis_client()
    store = JobResultStore(redis_client)
    publisher = EventPublisher(redis_client)

    def handle(fields: dict):
        process_job(fields["job_id"], fields["start_date"], store, publisher)

    log.info("schedule_worker_starting", consumer=CONSUMER_NAME)

    Worker(
        queue=ScheduleJobQueue(redis_client),
        handler=handle,
        consumer_name=CONSUMER_NAME,
    ).run()
