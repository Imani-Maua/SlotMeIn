import json
import redis
import structlog

log = structlog.get_logger()


class EventPublisher:
    """
    Publishes domain events to a single global Redis stream.

    Every event has a name and an arbitrary payload dict.
    Callers include relevant context in the payload (job_id, talent_id, etc).

    The stream is capped at MAX_LEN entries — Redis trims automatically.
    """

    STREAM = "slotmein:events"
    MAX_LEN = 1000

    def __init__(self, redisevent: redis.Redis):
        self.redisevent = redisevent

    def create_stream(self):
        if not self.redisevent.exists(self.STREAM):
            self.publish("stream.initialized")
            log.info("event_stream_created", stream=self.STREAM)

    def publish(self, event: str, payload: dict | None = None):
        self.redisevent.xadd(
            self.STREAM,
            {"event": event, "payload": json.dumps(payload or {})},
            maxlen=self.MAX_LEN,
            approximate=True,
        )

    def read(self, last_id: str, count: int = 100, block_ms: int = 5000) -> list[tuple[str, dict]]:
        messages = self.redisevent.xread({self.STREAM: last_id}, count=count, block=block_ms)
        if not messages:
            return []
        _, msgs = messages[0]
        return [(msg_id, fields) for msg_id, fields in msgs]
