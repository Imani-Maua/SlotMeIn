import pandas as pd
from datetime import timedelta, date, datetime, time
from collections import defaultdict
from sqlalchemy.orm import Session
from app.core.schedule.staffing.service import StaffingService
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.shifts.utils import flatten_shift_structure, start_date_within_allowed_window
from app.core.schedule.ml.tier_predictor import predict_tier
from app.core.utils.enums import Role




class ShiftSlotBuilder:

    def __init__(
        self,
        db: Session,
        start_date: date,
        occupancy_pct: float | None = None,
        temp_mean: float | None = None,
    ):
        self.db = db
        self.engine = StaffingService(db=self.db)
        self.start_date = start_date
        self.occupancy_pct = occupancy_pct
        self.temp_mean = temp_mean
        self.week_spec: dict = self._build_week_spec()

    def _ml_shift_type(self, period_roles: dict, period_id: int) -> str:
        """Determine "morning" or "afternoon" from the period's shift start time."""
        sample = next(iter(period_roles[period_id].values()))
        return "morning" if sample["start_time"] < time(12, 0) else "afternoon"

    def _build_week_spec(self) -> dict[date, dict[int, dict[str, dict]]]:
        start_date_within_allowed_window(start_date=self.start_date)
        end_date = self.start_date + timedelta(days=7)

        week = pd.date_range(self.start_date, end_date)
        week_spec = defaultdict(dict)
        period_roles = self.engine.generate_roles_per_shift()

        for dt in week:
            if self.occupancy_pct is not None:
                tier_override = {
                    period_id: predict_tier(
                        dt=dt.date(),
                        occupancy_pct=self.occupancy_pct,
                        shift=self._ml_shift_type(period_roles, period_id),
                        temp_mean=self.temp_mean,
                    )
                    for period_id in period_roles
                }
                staffed_periods = self.engine.apply_staffing_to_periods(
                    period_roles=period_roles,
                    tier_override=tier_override,
                )
            else:
                staffed_periods = self.engine.apply_staffing_to_periods(
                    period_roles=period_roles,
                    day=dt.strftime("%A"),
                )

            week_spec[dt.date()] = staffed_periods

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
                        role_name= Role(role),
                        role_count= role_data["count"]
                    )
                    flattened = flatten_shift_structure(shift_spec)
        
        return flattened

        






