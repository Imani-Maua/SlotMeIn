from datetime import date, timedelta
from fastapi import HTTPException, status
from app.database.models import ShiftPeriod
from app.core.schedule.shifts.schema import shiftSpecification


def start_date_within_allowed_window(start_date: date):
    """
    Ensures the schedule start date is:
    - Not in the past (no point generating a done week)
    - No more than 12 days in the future (prevents scheduling too far ahead)

    NOTE: original only blocked far-future dates, not past dates.
    Both guards are now enforced.
    """
    allowed_window = timedelta(days=12)
    if start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot generate a schedule for a past week"
        )
    if start_date > date.today() + allowed_window:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Schedule generation too far in the future (max 12 days ahead)"
        )


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

