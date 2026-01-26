from collections import defaultdict
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.shifts.schema import shiftSpecification
from datetime import date


class TalentByRole:
    @staticmethod
    def group_talents(talents: dict[int, talentAvailability]) -> dict[str, tuple[int, dict, str]]:
        """Group talents by their role.

        Args:
            talents (dict[int, talentAvailability]): Mapping of talent IDs to their availability objects.

        Returns:
            defaultdict[list]: Dictionary keyed by role name, where each value is a list of tuples
            containing (talent_id, availability_window, shift_name).
        """
        talents_by_role = defaultdict(list)
        for id, talent_info in talents.items():
            talents_by_role[talent_info.role.value].append((id, talent_info.window, talent_info.shift_name))
        return talents_by_role


class TalentGenerator():
    def __init__(self, shift: shiftSpecification, talents_by_role: dict[str, tuple[int, tuple]], lookup: dict[tuple[int, date], tuple[date, date]]):
        """Generate eligible talents for a given shift.

        Args:
            shift (shiftSpecification): The shift specification being assigned.
            talents_by_role (dict[str, tuple]): Mapping of role name to tuples of talent info.
            lookup (dict[tuple[int, date], tuple[date, date]]): Availability lookup keyed by (talent_id, date).
        """
        self.shift = shift
        self.talents_by_role = talents_by_role
        self.lookup = lookup

    def find_eligible_talents(self):
        """Find all eligible talents for the shift.

        Yields:
            int: Talent IDs that meet role, availability, and shift constraints.
        """
        seen = set()
        for talent_id, _, shifts in self.talents_by_role[self.shift.role_name]:
            window_lookup = self.lookup.get((talent_id, self.shift.start_time.date()), [])
            if any(start <= self.shift.start_time and end >= self.shift.end_time for start, end in window_lookup):
                if self.shift.shift_name in shifts:
                    if talent_id not in seen:
                        yield talent_id
                        seen.add(talent_id)

