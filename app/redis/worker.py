import signal
import threading
from typing import Callable

import structlog

from app.redis.job_queue import JobQueue

log = structlog.get_logger()


class Worker:
    """
    Handles the consume loop, crash recovery, graceful shutdown, and acking.
    Domain-specific logic lives entirely in the handler callable.

    Usage:
        def handle(fields: dict):
            process_something(fields["job_id"], fields["data"])

        Worker(queue=MyJobQueue(redisqueue), handler=handle, consumer_name="worker-1").run()
    """

    def __init__(self, queue: JobQueue, handler: Callable[[dict], None], consumer_name: str):
        self.queue = queue
        self.handler = handler
        self.consumer_name = consumer_name

    def run(self):
        self.queue.create_consumer_group()
        log.info("worker_started", stream=self.queue.stream, consumer=self.consumer_name)

        stop_event = threading.Event()

        def _request_shutdown(sig_num, stack_frame):
            log.info("manual shutdown requested")
            stop_event.set()

        signal.signal(signal.SIGINT, _request_shutdown)
        signal.signal(signal.SIGTERM, _request_shutdown)

        log.info("checking_pending_jobs")
        for msg_id, fields in self.queue.recover_orphaned_msgs(self.consumer_name):
            log.warning("recovering_stuck_job", job_id=fields.get("job_id"))
            try:
                self.handler(fields)
            finally:
                self.queue.ack(msg_id)

        while not stop_event.is_set():
            for msg_id, fields in self.queue.consume_msgs(self.consumer_name):
                if stop_event.is_set():
                    break
                try:
                    self.handler(fields)
                finally:
                    self.queue.ack(msg_id)
