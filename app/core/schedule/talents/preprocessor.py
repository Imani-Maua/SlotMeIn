from app.core.schedule.allocator.entities import weekRange
from app.database.models import TalentData
from app.core.utils.enums import ConstraintType
from app.core.schedule.talents.schema import TalentRecord
from app.core.schedule.talents.utils import fetch_all_shifts

class TalentPreprocessor:
    def __init__(self, week_provider: weekRange):
        self.week_provider = week_provider

    def preprocess(self, talent_rows: list[TalentData]) -> dict[int, TalentRecord]:
        records: dict[int, dict] = {}

        for row in talent_rows:
            tid = row.talent_id

            if tid not in records:
                records[tid] = {
                    "talent_id": tid,
                    "role": row.tal_role,
                    "weeklyhours": row.hours,
                    "constraint_status": bool(row.constraint_status),
                    "days": set(),
                    "shifts": set()
                }

            # If no constraint → assign later
            if not row.constraint_status:
                continue

            # Constrained logic
            constrained_talents = (row.constraint_type or "").lower()

            if constrained_talents == ConstraintType.COMBINATION.value:
                # Both day + shift defined
                records[tid]["days"].add(row.available_day)
                records[tid]["shifts"].add(row.available_shifts)

            elif constrained_talents == ConstraintType.SHIFT_RESTRICTION.value:
                # Shifts defined, days = all days
                records[tid]["shifts"].add(row.available_shifts)
                records[tid]["days"] = set(self.week_provider.get_date_map().keys())

            elif constrained_talents == ConstraintType.AVAILABILITY.value:
                # Availability defined by days only
                records[tid]["days"].add(row.available_day)
                # shifts = all shifts available
                # But only if not already set by combination
                if not records[tid]["shifts"]:
                    records[tid]["shifts"] = set(fetch_all_shifts())

        # Final conversion to dataclass-like record
        talent_objects: dict[int, TalentRecord] = {}
        for tid, record in records.items():
            if not record["constraint_status"]:
                # unconstrained:
                days = list(self.week_provider.get_date_map().keys())
                shifts = fetch_all_shifts()
            else:
                days = list(record["days"])
                shifts = list(record["shifts"])

            talent_objects[tid] = TalentRecord(
                talent_id=tid,
                role=record["role"],
                weeklyhours=record["weeklyhours"],
                constraint_status=record["constraint_status"],
                days=days,
                shifts=shifts
            )

        return talent_objects
    

