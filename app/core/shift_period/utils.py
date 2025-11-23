from sqlalchemy.orm import Query
from datetime import time
from app.database.models import ShiftTemplate, ShiftPeriod


def search_filters(query: Query,
                   shift_name: str | None = None,
                   start_time: time | None = None,
                   end_time: time | None = None):
    
    if shift_name:
        query = query.filter(ShiftPeriod.shift_name == shift_name)
    
    if start_time:
        query = query.filter(ShiftPeriod.start_time)
    
    if end_time:
        query = query.filter(ShiftPeriod.end_time)
    
    return query.all()