import redis
from app.redis.job_queue import JobQueue

class ScheduleEvent:
    JOB_STARTED    = "schedule.job.started"
    SOLVER_RUNNING = "schedule.solver.running"
    JOB_DONE       = "schedule.job.done"
    JOB_FAILED     = "schedule.job.failed"

class ScheduleJobQueue(JobQueue):
    """Job queue scoped to schedule generation."""

    STREAM = "schedule:jobs"
    GROUP  = "schedule-workers"

    def __init__(self, redisqueue: redis.Redis):
        super().__init__(redisqueue, stream=self.STREAM, group=self.GROUP)

    def publish(self, start_date: str) -> str:
        return super().publish_msgs({"start_date": start_date})
