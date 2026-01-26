from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment, underStaffedShifts
from app.core.schedule.allocator.engine.generators import TalentGenerator
from app.core.schedule.allocator.engine.validators import maxHoursValidator, consecutiveValidator, restValidator, dailyAssignmentValidator, context, abstractValidator
from app.core.schedule.allocator.engine.scheduler_scoring import computeScore, roundRobinPicker



class TalentAvailabilityService:
    def __init__(self, talent_availability: dict[int, talentAvailability], 
                 assignable_shifts: dict[int, shiftSpecification], 
                 talents_to_assign):
        
        self.availability = talent_availability
        self.assignable_shifts = assignable_shifts  
        self.talents_to_assign = talents_to_assign 

    def define_talent_availability_window(self):
        """
        Returns:
            dict[(talent_id, date), list[(start_dt, end_dt)]]
        """
        return {
            (tid, date): spans
            for tid, avail in self.availability.items()
            for date, spans in avail.window.items()
        }

    def define_talent_types(self):
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
        talent_types = self.define_talent_types()
        window = self.define_talent_availability_window()

        eligibility = {}

        for shift_instance_id, shift in self.assignable_shifts.items():
            gen = TalentGenerator(shift, self.talents_to_assign, window)
            candidates = list(gen.find_eligible_talents())

            prioritized = (
                [t for t in candidates if t in talent_types["constrained"]] +
                [t for t in candidates if t in talent_types["unconstrained"]]
            )

            eligibility[shift_instance_id] = prioritized

        return eligibility



class ScheduleBuilder:
    def __init__(self, availability: dict[int, talentAvailability], 
                 assignable_shifts: dict[int, shiftSpecification],
                talents_to_assign):
        self.availability = availability     # dict[int, talentAvailability]
        self.assignable_shifts = assignable_shifts  # dict[str, shiftSpecification]
        self.talents_to_assign = talents_to_assign

    def generate_schedule(self):
        plan = []

        availability_service = TalentAvailabilityService(
            self.availability, self.assignable_shifts, self.talents_to_assign
        )
        eligibility = availability_service.generate_eligible_talents()
        
        validators = [maxHoursValidator(), consecutiveValidator(), restValidator(), dailyAssignmentValidator()]

        for shift_instance_id, shift in self.assignable_shifts.items():
            candidates = eligibility.get(shift_instance_id, [])
            num_assigned = 0

            for talent_id in candidates:
                if num_assigned >= shift.role_count:
                    break

                scorer = computeScore(
                    shift=shift,
                    availability=self.availability,
                    assignments=plan,
                )
                top_candidates = scorer.getTopCandidates(candidates)

                round_robin = roundRobinPicker()
                best_fit = round_robin.pickBestFit(shift.role_name, top_candidates)

                ctx = context.contextFinder(talent_id, shift, self.availability, plan)

                # Check shift name validity
                if shift.shift_name not in self.availability[talent_id].shift_name:
                    continue

                # Validators
                if all(validator.can_assign_shift(ctx) for validator in validators):
                    
                    if best_fit == talent_id:

                        plan.append(
                            assignment(
                                talent_id=talent_id,
                                shift_id=shift_instance_id,  # now string
                                shift=shift                  # actual shiftSpecification object
                            )
                        )

                        # Mark assignment
                        for validator in validators:
                            if hasattr(validator, "mark_assigned"):
                                validator.mark_assigned(ctx)

                        num_assigned += 1

        return plan

    



class UnderstaffedShifts:
    def __init__(self, conn, assignable_shifts: dict[str, shiftSpecification], assigned_shifts: list[assignment]):
        self.conn = conn
        self.assignable_shifts = assignable_shifts
        self.assigned_shifts = assigned_shifts

    def get_all(self) -> list:
        understaffed = []

        assigned_count = {}
        for a in self.assigned_shifts:
            assigned_count[a.shift_id] = assigned_count.get(a.shift_id, 0) + 1

        for shift_id, shift in self.assignable_shifts.items():
            required = shift.role_count
            assigned = assigned_count.get(shift_id, 0)

            if assigned < required:
                understaffed.append(
                    underStaffedShifts(
                        shift_id=shift_id,           
                        shift_name=shift.shift_name,
                        shift_start=shift.start_time,
                        shift_end=shift.end_time,
                        role_name=shift.role_name,
                        required=required,
                        assigned=assigned,
                        missing=required - assigned,
                    )
                )

        return understaffed

    def unassigned_only(self):
        assigned_count = {a.shift_id: 1 for a in self.assigned_shifts}

        return [
            shift
            for shift_id, shift in self.assignable_shifts.items()
            if shift_id not in assigned_count
        ]
