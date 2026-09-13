from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from app.config.logging import configure_logging
from app.core.talents.routes import talents
from app.core.schedule.routes import schedule
from app.core.constraints.talent_constraints.routes import talent_constraints
from app.core.constraints.constraint_rules.routes import constraint_rules
from app.core.shift_template.routes import shift_templates
from app.core.shift_period.routes import shift_period
from app.authentication.routes import auth_router
from app.redis.client import create_redis_client
from app.core.schedule.events import ScheduleJobQueue
from app.redis.event_publisher import EventPublisher
from app.database.session import engine

configure_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("postgres_connected")
    except Exception as e:
        log.critical("postgres_connection_failed", error=str(e))
        raise

    try:
        redis_client = create_redis_client()
        redis_client.ping()
        log.info("redis_connected")
        ScheduleJobQueue(redis_client).create_consumer_group()
        EventPublisher(redis_client).ensure_stream()
        log.info("redis_streams_initialized")
        app.state.redis = redis_client
    except Exception as e:
        log.critical("redis_startup_failed", error=str(e))
        raise

    yield

    redis_client.close()
    log.info("redis_connection_closed")


app = FastAPI(title="SlotMeIn", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://slotmein.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/users")
app.include_router(talents, prefix="/talents")
app.include_router(talent_constraints, prefix="/talent_constraints")
app.include_router(constraint_rules, prefix="/constraint_rules")
app.include_router(shift_period, prefix="/shift_periods")
app.include_router(shift_templates, prefix="/shift_templates")
app.include_router(schedule, prefix="/schedule")
