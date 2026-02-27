from datetime import datetime, date

from app.core.schedule.talents.schema import talentAvailability, TalentRecord
from app.core.schedule.allocator.entities import weekRange
from app.core.schedule.talents.utils import map_shift_name_to_time
from app.core.utils.enums import Role

class TalentAssembler:
    def __init__(self, week_provider: weekRange):
        self.week_provider = week_provider
        self.date_map = week_provider.get_date_map()

    def assemble(self, records: dict[int, TalentRecord]) -> dict[int, talentAvailability]:
        result: dict[int, talentAvailability] = {}

        for tid, record in records.items():
            window: dict[date, list[tuple[datetime, datetime]]] = {}

            for day in record.days:
                d: date = self.date_map[day]
                window[d] = []

                for shift in record.shifts:
                    span = map_shift_name_to_time(shift)
                    if not span:
                        continue

                    start_t, end_t = span

                    # Combine date + time into datetime
                    start_dt = datetime.combine(d, start_t)
                    end_dt   = datetime.combine(d, end_t)

                    window[d].append((start_dt, end_dt))

            result[tid] = talentAvailability(
                talent_id=record.talent_id,
                constraint=record.constraint_status,
                role=Role(record.role),
                shift_name=record.shifts,
                window=window,
                weeklyhours=record.weeklyhours
            )

        return result

