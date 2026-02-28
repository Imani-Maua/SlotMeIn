from sqlalchemy.orm import Query
from datetime import time
from app.database.models import ShiftTemplate, ShiftPeriod


def search_filters(query: Query,
                   shift_name: str | None = None,
                   shift_start: time | None = None,
                   shift_end: time | None = None):
    
    if shift_name:
        query = query.filter(ShiftPeriod.shift_name == shift_name)
    
    if shift_start:
        query = query.filter(ShiftTemplate.shift_start == shift_start)
    
    if shift_end:
        query = query.filter(ShiftTemplate.shift_end == shift_end)
    
    return query.all()