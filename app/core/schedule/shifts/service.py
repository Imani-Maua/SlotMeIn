import pandas as pd
from datetime import timedelta, date, datetime
from collections import defaultdict
from sqlalchemy.orm import Session
from app.core.schedule.staffing.service import StaffingService
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.shifts.utils import flatten_shift_structure




class ShiftSlotBuilder:

    def __init__(self, db: Session, start_date: date):
        self.db = db
        self.engine = StaffingService(db=self.db)
        self.start_date = start_date
        self.week_spec: dict = self._build_week_spec()

    def _build_week_spec(self) -> dict [date, dict[int, dict[str, dict]]]:
       #validate_week_start(start_date=start_date)
        #start_date_within_allowed_window(start_date=self.start_date)
        end_date = self.start_date + timedelta(days=7)

        week = pd.date_range(self.start_date, end_date)

        week_spec = defaultdict(dict)
        period_roles = self.engine.generate_roles_per_shift()

        for date in week:
            day_name = date.strftime("%A")

            
            staffed_periods = self.engine.apply_staffing_to_periods(period_roles=period_roles, day=day_name)
            week_spec[date.date()] = staffed_periods
        
        return week_spec
    
    def build_week_slots(self) -> dict[int, shiftSpecification]:
        shift_spec = defaultdict(lambda: defaultdict(dict))


        for shift_date, staffed_periods in self.week_spec.items():
            staffed_periods: dict
            for period_id, staffed_roles in staffed_periods.items():
                staffed_roles: dict
                for role, role_data in staffed_roles.items():
                    role_data: dict
                    shift_spec[shift_date][period_id][role] = shiftSpecification(
                        template_id=role_data["template_id"],
                        start_time=datetime.combine(shift_date, role_data["start_time"]),
                        end_time=datetime.combine(shift_date, role_data["end_time"]),
                        shift_name= role_data["shift_name"],
                        role_name= role,
                        role_count= role_data["count"]
                    )
                    flattened = flatten_shift_structure(shift_spec)
        
        return flattened

        






