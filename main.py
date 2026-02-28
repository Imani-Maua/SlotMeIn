from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.talents.routes import talents
from app.core.schedule.routes import schedule
from app.core.constraints.talent_constraints.routes import talent_constraints
from app.core.constraints.constraint_rules.routes import constraint_rules
from app.core.shift_template.routes import shift_templates
from app.core.shift_period.routes import shift_period
from app.authentication.routes import auth_router


app = FastAPI(title="SlotMeIn", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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









