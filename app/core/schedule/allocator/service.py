from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.engine.utils import get_break_duration
from ortools.sat.python import cp_model
from datetime import timedelta, date, datetime
from app.core.schedule.allocator.utils import (talent_eligible_for_shift, 
                                               is_talent_assigned, 
                                               group_shifts_by_date, 
                                               find_last_shift_end,
                                               days_worked_in_history)


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
        # ---------------------------------------------------------------
        # Constraint Three: dailyAssignmentValidator → 1 shift per talent per day (hard)
        # ---------------------------------------------------------------
        for tid in talent_ids:
            for _, date_sids in shifts_by_date.items():
                date_vars = [
                    assigned[tid][sid]
                    for sid in date_sids
                    if sid in assigned.get(tid, {})
                ]
                if date_vars:
                    model.add(sum(date_vars) <= 1)
        
        # ---------------------------------------------------------------
        # Constraint Four: restValidator → 11-hour rest between days (hard)
        # ---------------------------------------------------------------
        for tid in talent_ids:
            for sid in shift_ids:
                shift = self.assignable_shifts[sid]
                if sid not in assigned.get(tid, {}):
                    continue
                
                shift_date = shift.start_time.date()
                prev_date = shift_date - timedelta(days=1)
                prev_date_shift_end = find_last_shift_end(talent_id=tid, on_date=prev_date, history=self.history)


                if prev_date_shift_end is None:
                    for prev_sid in shifts_by_date.get(prev_date, []):
                        if prev_sid not in assigned.get(tid, {}):
                            continue

                        prev_shift = self.assignable_shifts[prev_sid]
                        rest = (shift.start_time - prev_shift.end_time).total_seconds()/ 3600

                        if rest < MIN_REST_HOURS:
                            model.add(assigned[tid][sid] + assigned[tid][prev_sid] <= 1)
                        
                else:
                    rest = (shift.start_time - prev_shift.end_time).total_seconds()/ 3600
                    if rest < MIN_REST_HOURS:
                        model.add(assigned[tid][sid] == 0)
        
        # ---------------------------------------------------------------
        # Constraint Five: constrained talents first
        # ---------------------------------------------------------------

        # this is implicitly enforced by MRV within the model, but the system needs a 
        # guarantee that constrained talents are going to be filled first
        fill_term_bonus = []
        for tid in talent_ids:
            talent = self.availability[tid]
            if talent.constraint:
                for sid in shift_ids:
                    for slot in range(self.assignable_shifts[sid].role_count):
                        if slot in slot_assignments[tid].get(sid, {}):
                            fill_term_bonus.append(slot_assignments[tid][sid][slot])
        

        # ---------------------------------------------------------------
        # Constraint Six: max 6 consecutive days
        # ---------------------------------------------------------------
        all_dates = sorted(shifts_by_date.keys())
        first_date = all_dates[0] if all_dates else None


        day_indicators: dict[int, dict[date, cp_model.IntVar]] = {}


        for tid in talent_ids:
            day_indicators[tid] = {}
            for day_date in all_dates:
                day_vars = [
                    assigned[tid][sid]
                    for sid in shifts_by_date.get(day_date, [])
                    if sid in assigned.get(tid, [])
                ]
                if day_vars:
                    indicator = model.new_bool_var(f"talent_{tid}works_date{day_date.isoformat()}")
                    model.add(sum(day_vars) == indicator)
                    day_indicators[tid][day_date] = indicator
        
        
        for tid in talent_ids:
            history_dates = days_worked_in_history(tid, self.history)
            streak = 0

            if first_date:
                day_in_streak = first_date - timedelta(days=1)
                while day_in_streak in history_dates:
                    streak += 1
                    day_in_streak -= timedelta(days=1)
            
            if first_date is None:
                continue

            window_start = first_date - timedelta(days=streak)

            last_date = all_dates[-1]

            current = window_start
            while current <= last_date:
                window_dates = [current + timedelta(days=day) for day in range(7)]
 
                window_solver_vars = []
                fixed_days_worked  = 0
 
                for window in window_dates:
                    if window in history_dates:
                        # Fixed fact — counts as 1 worked day
                        fixed_days_worked += 1
                    elif window in day_indicators[tid]:
                        # Solver variable — undecided
                        window_solver_vars.append(day_indicators[tid][window])
                    # else: no shift on this date, contributes 0
 
                # Total days worked in window =
                #   fixed_days_worked + sum(window_solver_vars)
                # This must not exceed MAX_CONSECUTIVE_DAYS (6)
                remaining = MAX_CONSECUTIVE_DAYS - fixed_days_worked
                if remaining <= 0:
                    # History alone already fills the window —
                    # block all solver days in this window
                    for vars in window_solver_vars:
                        model.add(vars == 0)
                elif window_solver_vars:
                    model.add(sum(window_solver_vars) <= remaining)
 
                current += timedelta(days=1)