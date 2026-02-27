from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import enum
import pandas as pd
from app.core.utils.enums import Role


@dataclass
class shiftSpecification:
    start_time: datetime
    end_time: datetime
    shift_name: str
    role_name: Role
    role_count: int



@dataclass
class assignment:
    talent_id : int
    shift_id: int
    shift : shiftSpecification

@dataclass
class weekRange:
    start_date: date | str
    week: list[date] = field(init=False)
    date_map: dict[str, date] = field(init=False)

    def __post_init__(self):
        # Normalize input
        start = pd.to_datetime(self.start_date).date()

        # Snap to Sunday (weekday(): Monday=0 … Sunday=6)
        # If not Sunday, subtract days back to Sunday
        if start.weekday() != 6:
            start = start - timedelta(days=(start.weekday() + 1))

        # Build 7-day week (Sunday → Saturday)
        self.week = [start + timedelta(days=i) for i in range(7)]

        # Safe mapping: NO overwriting ever
        # Sunday, Monday, Tuesday, ... Saturday
        self.date_map = {
            day.strftime("%A"): day for day in self.week
        }

    def get_week(self) -> list[date]:
        return self.week

    def get_date_map(self) -> dict[str, date]:
        return self.date_map



@dataclass
class underStaffedShifts:
    shift_id: int
    shift_name: str
    shift_start: datetime
    shift_end: datetime
    role_name: str
    required: int
    assigned: int
    missing: int



