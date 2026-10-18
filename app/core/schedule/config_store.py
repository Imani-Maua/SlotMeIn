import json
import redis
from app.core.schedule.schema import SchedulerConfig


_KEY = "schedule:config"


class SchedulerConfigStore:

    def __init__(self, client: redis.Redis):
        self._redis = client

    def get(self) -> SchedulerConfig:
        raw = self._redis.get(_KEY)
        if raw is None:
            return SchedulerConfig()
        return SchedulerConfig.model_validate_json(raw)

    def save(self, config: SchedulerConfig) -> None:
        self._redis.set(_KEY, config.model_dump_json())
