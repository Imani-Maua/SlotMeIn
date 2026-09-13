import redis
from redis import exceptions
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Generic Redis stream job queue.

    Producers call publish_event(), consumers call consume_event() in a loop then ack().
    Pass stream and group to scope this queue to a specific job type.

    Example:
        queue = JobQueue(redisqueue, stream="schedule:jobs", group="schedule-workers")
        queue = JobQueue(redisqueue, stream="notification:jobs", group="notification-workers")
    """

    MAX_RETRIES = 3

    def __init__(self, redisqueue: redis.Redis, stream: str, group: str):
        self.redisqueue = redisqueue
        self.stream = stream
        self.group = group
        self.dlq = f"{stream}:dlq"

    def create_consumer_group(self):
        """
        Create the consumer group if it doesn't exist yet.
        Safe to call on every startup — silently skips if already created.
        """
        try:
            self.redisqueue.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except exceptions.ResponseError:
            pass

    def publish_msgs(self, fields: dict) -> str:
        """
        Add a job to the stream. Returns an auto-generated job_id.
        fields: arbitrary payload for the worker to read.
        """
        job_id = str(uuid4())
        self.redisqueue.xadd(self.stream, {"job_id": job_id, **fields})
        return job_id

    def consume_msgs(self, consumer_name: str, block_ms: int = 5000):
        """
        Read the next undelivered message from the stream.
        Blocks up to block_ms milliseconds waiting for one.

        Yields (msg_id, fields) for each message received.
        The caller must call ack(msg_id) when processing is complete.
        """
        messages = self.redisqueue.xreadgroup(
            groupname=self.group,
            consumername=consumer_name,
            streams={self.stream: ">"},
            count=1,
            block=block_ms,
        )
        if not messages:
            return
        for _, msgs in messages:
            for msg_id, fields in msgs:
                yield msg_id, fields

    def recover_orphaned_msgs(self, consumer_name: str):
        """
        Yield pending messages from a previous run that were never acked.

        Before re-delivering, checks delivery counts via XPENDING. Messages
        that have exceeded MAX_RETRIES are moved to the DLQ and acked off
        the main stream — they will not be retried again.
        """
        while True:
            pending = self.redisqueue.xpending_range(
                self.stream, self.group, min="-", max="+", count=10, consumername=consumer_name,
            )
            if not pending:
                return

            dead = [pend for pend in pending if pend["times_delivered"] > self.MAX_RETRIES]
            for pending in dead:
                msg_id = pending["message_id"]
                msgs = self.redisqueue.xrange(self.stream, msg_id, msg_id, count=1)
                if msgs:
                    _, fields = msgs[0]
                    self.redisqueue.xadd(self.dlq, fields)
                    logger.error(
                        "job %s moved to DLQ after %d delivery attempts",
                        fields.get("job_id", msg_id),
                        pending["times_delivered"],
                    )
                self.redisqueue.xack(self.stream, self.group, msg_id)

            messages = self.redisqueue.xreadgroup(
                groupname=self.group,
                consumername=consumer_name,
                streams={self.stream: "0"},
                count=10,
            )
            if not messages or not messages[0][1]:
                return
            for _, msgs in messages:
                for msg_id, fields in msgs:
                    yield msg_id, fields

    def ack(self, msg_id: str):
        """Acknowledge that a message has been successfully processed."""
        self.redisqueue.xack(self.stream, self.group, msg_id)
