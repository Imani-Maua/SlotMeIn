from datetime import timedelta
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment



class computeScore:
    """Scoring engine to evaluate how well a talent fits a given shift.

    The score considers:
    - Remaining weekly hours compared to hours already assigned.
    - Recent work streaks and rest days.
    - Minimum rest hours between consecutive shifts.
    """

    def __init__(self, shift: shiftSpecification, availability: dict[int, talentAvailability], assignments: list[assignment]):
        """
        Args:
            shift (shiftSpecification): 
                The shift being evaluated.
            availability (dict[int, talentAvailability]): 
                Mapping of talent IDs to their availability and weekly hours.
            assignments (list[assignment]): 
                List of existing assignments to use when checking workload and streaks.
        """
        self.shift = shift
        self.availability = availability
        self.assignments = assignments

    def calculate_score(self, talent_id: int) -> float:
        """Calculate the score for a single talent.

        Args:
            talent_id (int): The ID of the talent to score.

        Returns:
            float: A numerical score representing how suitable the talent is 
                   for the given shift. Higher is better.
        """
        score = 0

        
        weekly_hours = self.availability[talent_id].weeklyhours
        hours_assigned = sum(
            (a.shift.end_time - a.shift.start_time).total_seconds()/3600
        for a in self.assignments if a.talent_id == talent_id)
        remaining = weekly_hours - hours_assigned
        score += remaining

        
        current_day = self.shift.start_time.date()
        work_streak = 1
        rest_streak = 0
        for delta in range(1,7):
            prev_day = current_day - timedelta(days=delta)
            had_shift =  any(a.talent_id == talent_id and a.shift.start_time.date() == prev_day for a in self.assignments)
            if had_shift:
                work_streak += 1
            else:
                rest_streak += 1

        score -= (work_streak * 2)
        score += (rest_streak * 2)

        yesterday = current_day - timedelta(days=1)
        
        yesterday_shift = next(
            (a.shift for a in self.assignments if a.talent_id == talent_id and a.shift.start_time.date() == yesterday), 
            None)
        if yesterday_shift:
            rest_hours = (self.shift.start_time - yesterday_shift.end_time).total_seconds()/3600
            if rest_hours < 11:
                score -= 5

        return score

    def getTopCandidates(self, eligible_talents: list[int]) -> list[int] | None:
        """Return the top-scoring candidates from a list of eligible talents.

        Args:
            eligible_talents (list[int]): List of talent IDs eligible for the shift.

        Returns:
            list[int] | None: List of IDs with the highest score, 
                              or None if no eligible talents.
        """
        if not eligible_talents:
            return None
        
        scored = [(tid, self.calculate_score(tid)) for tid in eligible_talents]
        scored.sort(key=lambda x: x[1], reverse=True)

        top_score = scored[0][1]
        return [tid for tid, s in scored if s == top_score]

class roundRobinPicker:
    """Round-robin picker to fairly distribute assignments among top candidates."""
    def __init__(self):
        """Initialize the pointer tracker for each role."""
        self.pointers = {}

    def pickBestFit(self, role: str, candidates: list[int]) -> int | None:
        """Pick the best fit candidate for a role using round-robin.

        Args:
            role (str): The role name being filled (e.g., 'hostess', 'bartender').
            candidates (list[int]): List of candidate IDs with equal top score.

        Returns:
            int | None: The chosen candidate ID, or None if no candidates.
        """
        if not candidates:
            return None
        idx = self.pointers.get(role, 0) % len(candidates)
        chosen = candidates[idx]

        self.pointers[role] = (idx + 1) % len(candidates)
        return chosen
