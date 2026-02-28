from app.core.schedule.allocator.entities import weekRange
from app.database.models import TalentData
from app.core.utils.enums import ConstraintType
from app.core.schedule.talents.schema import TalentRecord
from app.core.schedule.talents.utils import fetch_all_shifts


class TalentPreprocessor:
    """
    Converts raw talent_data view rows into TalentRecord objects.

    IMPORTANT TO UNDERSTAND: This confused me when developing frontend.
    All constraint types are WHITELISTS — the manager selects what the talent
    CAN do, not what they cannot:
      - availability:       These are the days the person works (their working days)
      - shift restriction:  These are the shifts the person can be assigned
      - combination:        This is the exact day + shift combination they work
    """

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

            constrained_talents = (row.constraint_type or "").lower()

            if constrained_talents == ConstraintType.COMBINATION.value:
                # Manager picks the day + shift this person works
                records[tid]["days"].add(row.available_day)
                records[tid]["shifts"].add(row.available_shifts)

            elif constrained_talents == ConstraintType.SHIFT_RESTRICTION.value:
                # Manager picks the shifts this person can work; available all days
                records[tid]["shifts"].add(row.available_shifts)
                records[tid]["days"] = set(self.week_provider.get_date_map().keys())

            elif constrained_talents == ConstraintType.AVAILABILITY.value:
                # Manager picks the days this person works; available for all shifts
                records[tid]["days"].add(row.available_day)
                if not records[tid]["shifts"]:
                    records[tid]["shifts"] = set(fetch_all_shifts())

        
        talent_objects: dict[int, TalentRecord] = {}
        all_week_days = set(self.week_provider.get_date_map().keys())

        for tid, record in records.items():
            if not record["constraint_status"]:
                
                days = list(all_week_days)
                shifts = fetch_all_shifts()
            else:
                days = list(record["days"]) if record["days"] else list(all_week_days)
                shifts = list(record["shifts"]) if record["shifts"] else fetch_all_shifts()

            talent_objects[tid] = TalentRecord(
                talent_id=tid,
                role=record["role"],
                weeklyhours=record["weeklyhours"],
                constraint_status=record["constraint_status"],
                days=days,
                shifts=shifts
            )

        return talent_objects
