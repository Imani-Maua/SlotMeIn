from datetime import time, date
from collections import defaultdict
from app.core.utils.enums import Shifts, Days, ConstraintType
from app.core.schedule.allocator.entities import weekRange
from app.database.models import TalentData

def map_shift_name_to_time(shift_name: str | None):
    if shift_name:
        shift_name = shift_name.lower()
    lookup = {
        Shifts.AM.value: (time(6,0), time(15,0)),
        Shifts.PM.value: (time(15,0), time(23,30)),
        Shifts.LOUNGE.value: (time(11,0), time(23,59))
    }
    return lookup.get(shift_name)

def fetch_all_shifts():
    return [shift.value for shift in Shifts]

def fetch_all_days():
    return [day.value for day in Days]

def build_window_for_row(row: TalentData, 
                         week_provider: weekRange, 
                         full_week: list[date],
                         all_shifts: list[Shifts]) -> dict:
    window = defaultdict(list)

    constraint_type = row.constraint_type
    day = row.available_day      # Usually a weekday string
    shifts = row.available_shifts

    # COMBINATION: specific day + specific shifts
    if constraint_type == ConstraintType.COMBINATION.value:
        if day:
            date = week_provider.get_date_map()[day].date()
            for shift in shifts:
                window[date].append(map_shift_name_to_time(shift))

    # AVAILABILITY: specific day + all shifts
    elif constraint_type == ConstraintType.AVAILABILITY.value:
        if day:
            date = week_provider.get_date_map()[day].date()
            for shift in all_shifts:
                window[date].append(map_shift_name_to_time(shift))

    # SHIFT RESTRICTION: all days + specific shifts
    elif constraint_type == ConstraintType.SHIFT_RESTRICTION.value:
        for date in full_week:  # already a date object
            for shift in shifts:
                window[date].append(map_shift_name_to_time(shift))

    # Fallback → all days, all shifts
    else:
        for date in full_week:
            for shift in all_shifts:
                window[date].append(map_shift_name_to_time(shift))

    return dict(window)
