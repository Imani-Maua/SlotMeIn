from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.engine.utils import get_break_duration
from ortools.sat.python import cp_model
from datetime import timedelta, date, datetime
from app.core.schedule.allocator.utils import talent_eligible_for_shift, is_talent_assigned, group_shifts_by_date, find_last_shift_end


MIN_REST_HOURS = 11
MAX_CONSECUTIVE_DAYS = 6
SCALE = 100 #cp-sat works with integers only

#hours beyond contracted hours * this factor get penalised steeply
OVERWORK_THRESHOLD = 1.15

#Objective weights

CONSTRAINED_FILL_BONUS = 50
FILL_WEIGHT = 200 #reward per filled slot
UNDERWORK_PENALTY = 80     #Penalty per centihour below contracted hours
MILD_OVERWORK_PENALTY = 20 #Penalty per centihour in acceptable overwork band
STEEP_OVERWORK_PENALTY = 100 #penalty per centihour in excessive overwork band 


class CSPScheduler:

    def __init__(self, availability: dict[int, talentAvailability], 
                 assignable_shifts: dict[int, shiftSpecification],
                 talents_to_assign,
                 history: list[assignment] = None):
        
        self.availability = availability
        self.assignable_shifts = assignable_shifts
        self.talents_to_assign = talents_to_assign
        self.history = history or []

    def generate_schedule(self) -> list[assignment]:


        model = cp_model.CpModel()
        shift_ids = list(self.assignable_shifts.keys())
        talent_ids = list(self.availability.keys())

        # ----------------------------------------------------------
        # Decision variables
        # slot_assignments[tid][sid][slot] ∈ {0,1}  — 1 = talent fills slot
        # ----------------------------------------------------------

        slot_assignments = {}
        for tid in talent_ids:
            slot_assignments[tid] = {}
            for sid in shift_ids:
                shift = self.assignable_shifts[sid]
                talent = self.availability[tid]
                slot_assignments[tid][sid] = {}
                if talent_eligible_for_shift(talent, shift):
                    for slot in range(shift.role_count):
                        slot_assignments[tid][sid][slot] = model.new_bool_var(f"slot_assignments_for_talent{tid}_to_shift{sid}_for_slot{slot}")
        

      # ----------------------------------------------------------
        # Constraint One: Each slot filled by at most one talent
        # ----------------------------------------------------------

        for sid in shift_ids:
            shift = self.assignable_shifts[sid]
            for slot in range(shift.role_count):
                slot_vars = [
                    slot_assignments[tid][sid][slot]
                    for tid in talent_ids
                    if slot in slot_assignments[tid].get(sid, {})
                ]
                if slot_vars:
                    model.add(sum(slot_vars) <= 1)
        
         # ----------------------------------------------------------
        # Constraint Two: Each talent fills at most 1 slot per shift instance
        # ----------------------------------------------------------

        for tid in talent_ids:
            for sid in shift_ids:
                shift = self.assignable_shifts[sid]
                talent_slots = [
                    slot_assignments[tid][sid][slot]
                    for slot in range(shift.role_count)
                    if slot in slot_assignments[tid].get(sid, {})
                ]
                if len(talent_slots) > 1:
                    model.add(sum(talent_slots) <= 1)
          # ----------------------------------------------------------
        # Convenience indicator: assigned[tid][sid] = 1 if talent works shift otherwise 0
        # ----------------------------------------------------------

        assigned = {}
        for tid in talent_ids:
            assigned[tid] = {}
            for sid in shift_ids:
                shift = self.assignable_shifts[sid]
                talent_slots = [
                    slot_assignments[tid][sid][slot]
                    for slot in range(shift.role_count)
                    if slot in slot_assignments[tid.get(sid, {})]
                ]
                if talent_slots:
                    assigned[tid][sid] = is_talent_assigned(talent_id=tid, shift_id=sid, talent_slots=talent_slots, model=model)
        
        shifts_by_date = group_shifts_by_date(shift_ids=shift_ids, assignable_shifts=self.assignable_shifts)
        
