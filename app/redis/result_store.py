import json
import redis


class JobResultStore:
    """
    Owns all result state for scheduled jobs.

    Results live in Redis hashes keyed by job_id and expire after TTL seconds.
    Status lifecycle: pending → running → done | failed
    """

    TTL = 3600  

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def _key(self, job_id: str) -> str:
        return f"schedule:result:{job_id}"

    def set_pending(self, job_id: str):
        key = self._key(job_id)
        self.redis_client.hset(key, mapping={"status": "pending"})
        self.redis_client.expire(key, self.TTL)

    def set_running(self, job_id: str):
        self.redis_client.hset(self._key(job_id), "status", "running")

    def set_done(self, job_id: str, result: dict):
        self.redis_client.hset(self._key(job_id), mapping={
            "status": "done",
            "result": json.dumps(result),
        })

    def set_failed(self, job_id: str, error: str):
        self.redis_client.hset(self._key(job_id), mapping={
            "status": "failed",
            "error": error,
        })

    def get(self, job_id: str) -> dict | None:
        """
        Returns the full job state, or None if the job_id is unknown / expired.
        The 'result' field is deserialized from JSON if present.
        """
        data = self.redis_client.hgetall(self._key(job_id))
        if not data:
            return None
        if "result" in data:
            data["result"] = json.loads(data["result"])
        return data
