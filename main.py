from fastapi import FastAPI
from app.core.talents.routes import talents
from app.core.constraints.talent_constraints.routes import talent_constraints
from app.core.constraints.constraint_rules.routes import constraint_rules
from app.core.shift_template.routes import shift_templates
from app.core.shift_period.routes import shift_period
from app.authentication.routes import auth_router


app = FastAPI(title="Shiftly", version="1.0")


app.include_router(talents, prefix="/talents")
app.include_router(talent_constraints, prefix="/talent_constraints")
app.include_router(constraint_rules, prefix="/constraint_rules")
app.include_router(shift_period, prefix="/shift_period")
app.include_router(shift_templates, prefix="/shift_templates")
app.include_router(auth_router, prefix="/users")









