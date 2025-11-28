from datetime import date, timedelta
from fastapi import HTTPException, status
from app.database.models import ShiftPeriod
from app.core.schedule.shifts.schema import shiftSpecification

def validate_week_start(start_date: date):
    if start_date.strftime("%A") is not "Monday":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="The start date of the schedule is Monday")
    
def start_date_within_allowed_window(start_date: date):
    allowed_window = timedelta(days=12)
    if start_date > date.today() + allowed_window:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Schedule generation too far in the future")

def flatten_shift_structure(week_spec):
    flattened = {}

    for shift_date, periods in week_spec.items():
        for period_id, roles in periods.items():
            for role_name, spec in roles.items():

                template_id = spec.template_id

                shift_instance_id = f"{template_id}__{shift_date}__{period_id}__{role_name}"

                flattened[shift_instance_id] = shiftSpecification(
                    template_id=template_id,
                    start_time=spec.start_time,
                    end_time=spec.end_time,
                    shift_name=spec.shift_name,
                    role_name=spec.role_name,
                    role_count=spec.role_count,
                )

    return flattened

