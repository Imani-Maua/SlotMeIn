from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment, underStaffedShifts
from app.core.schedule.allocator.engine.generators import TalentGenerator
from app.core.schedule.allocator.engine.validators import consecutiveValidator, restValidator, dailyAssignmentValidator, context
from app.core.schedule.allocator.engine.utils import get_break_duration



class TalentAvailabilityService:
    def __init__(self, talent_availability: dict[int, talentAvailability], 
                 assignable_shifts: dict[int, shiftSpecification], 
                 talents_to_assign):
        
        self.availability = talent_availability
        self.assignable_shifts = assignable_shifts  
        self.talents_to_assign = talents_to_assign 

    def _define_talent_availability_window(self):
        """
        Returns:
            dict[(talent_id, date), list[(start_dt, end_dt)]]
        """
        return {
            (tid, date): spans
            for tid, avail in self.availability.items()
            for date, spans in avail.window.items()
        }

    def _define_talent_types(self):
        return {
            "constrained": [t.talent_id for t in self.availability.values() if t.constraint],
            "unconstrained": [t.talent_id for t in self.availability.values() if not t.constraint],
        }

    def generate_eligible_talents(self):
        """
        Returns:
            dict[str, list[int]]
            shift_instance_id → [talent_ids]
        """
        talent_types = self._define_talent_types()
        window = self._define_talent_availability_window()

        eligibility = {}

        for shift_instance_id, shift in self.assignable_shifts.items():
            gen = TalentGenerator(shift, self.talents_to_assign, window)
            candidates = list(gen.find_eligible_talents())

            prioritized = (
                [talent for talent in candidates if talent in talent_types["constrained"]] +
                [talent for talent in candidates if talent in talent_types["unconstrained"]]
            )

            eligibility[shift_instance_id] = prioritized

        return eligibility



class ScheduleBuilder:
    def __init__(self):
        pass

        

    def generate_schedule(self):
        pass