from datetime import date, timedelta
from fastapi import HTTPException, status
from app.database.models import ShiftPeriod

def validate_week_start(start_date: date):
    if start_date.strftime("%A") is not "Monday":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="The start date of the schedule is Monday")
    
def start_date_within_allowed_window(start_date: date):
    allowed_window = timedelta(days=12)
    if start_date > date.today() + allowed_window:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Schedule generation too far in the future")


