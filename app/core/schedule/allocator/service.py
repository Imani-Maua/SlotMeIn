from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.utils import get_break_duration
from ortools.sat.python import cp_model
from datetime import timedelta, date
from app.core.schedule.allocator.utils import (talent_eligible_for_shift, 
                                               group_shifts_by_date, 
                                               find_last_shift_end,
                                               days_worked_in_history,
                                               week_start_for_date,
                                               shift_duration_hours)


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
    
    def _build_variables(self, model: cp_model.CpModel, shift_ids: list[int], talent_ids: list[int]) -> dict[int, dict[int, dict[int, cp_model.IntVar]]]:
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
        return slot_assignments
    
    def _build_constraints(self, model: cp_model.CpModel, 
                           shift_ids: list[int],
                           talent_ids: list[int], 
                           slot_assignments: dict[int, dict[int, dict[int, cp_model.IntVar]]],
                           is_assigned: dict[int, dict[int, cp_model.IntVar]]):
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

        # ---------------------------------------------------------------
        # Constraint Three: dailyAssignmentValidator → 1 shift per talent per day (hard)
        # ---------------------------------------------------------------
        shifts_by_date = group_shifts_by_date(shift_ids=shift_ids, assignable_shifts=self.assignable_shifts)
        for tid in talent_ids:
            for _, date_sids in shifts_by_date.items():
                date_vars = [
                    is_assigned[tid][sid]
                    for sid in date_sids
                    if sid in is_assigned.get(tid, {})
                ]
                if date_vars:
                    model.add(sum(date_vars) <= 1)
        
         # ---------------------------------------------------------------
        # Constraint Four: restValidator → 11-hour rest between days (hard)
        # ---------------------------------------------------------------
        for tid in talent_ids:
            for sid in shift_ids:
                shift = self.assignable_shifts[sid]
                if sid not in is_assigned.get(tid, {}):
                    continue
                
                shift_date = shift.start_time.date()
                prev_date = shift_date - timedelta(days=1)
                prev_date_shift_end = find_last_shift_end(talent_id=tid, on_date=prev_date, history=self.history)


                if prev_date_shift_end is None:
                    for prev_sid in shifts_by_date.get(prev_date, []):
                        if prev_sid not in is_assigned.get(tid, {}):
                            continue

                        prev_shift = self.assignable_shifts[prev_sid]
                        rest = (shift.start_time - prev_shift.end_time).total_seconds()/ 3600

                        if rest < MIN_REST_HOURS:
                            model.add(is_assigned[tid][sid] + is_assigned[tid][prev_sid] <= 1)
                        
                else:
                    rest = (shift.start_time - prev_date_shift_end).total_seconds()/ 3600
                    if rest < MIN_REST_HOURS:
                        model.add(is_assigned[tid][sid] == 0)
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
                    is_assigned[tid][sid]
                    for sid in shifts_by_date.get(day_date, [])
                    if sid in is_assigned.get(tid, [])
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
        

    def _convenience_methods(self, slot_assignments: dict[int, dict[int, dict[int, cp_model.IntVar]]], model: cp_model.CpModel) -> dict[int, dict[int, cp_model.IntVar]]:
        # This is not a constraint, but it is a convenient way to refer to whether a talent is assigned to a shift anywhere in the model
        # It allows us to easily apply penalties/rewards in the objective function based on whether a talent is working a shift, without having to sum over all their slots every time
        assigned = {}
        for tid in self.availability.keys():
            assigned[tid] = {}
            for sid in self.assignable_shifts.keys():
                talent_slots = [
                    slot_assignments[tid][sid][slot]
                    for slot in range(self.assignable_shifts[sid].role_count)
                    if slot in slot_assignments[tid].get(sid, {})
                ]
                if talent_slots:
                    assigned[tid][sid] = model.new_bool_var(f"assigned_talent{tid}_shift{sid}")
                    model.add(sum(talent_slots) == assigned[tid][sid])
        return assigned
    
    def _build_objective(self, 
                          model: cp_model.CpModel, 
                          assigned: dict[int, dict[int, cp_model.IntVar]],
                          shift_ids: list[int],
                          talent_ids: list[int],
                          slot_assignments: dict[int, dict[int, dict[int, cp_model.IntVar]]]) -> list[assignment]:
        
        
        # Collect every single slot assignment variable into a single flat list. 
        # Variables in fill-terms are either a 0 or 1 decision that the solver is going to make.
        fill_terms = []
        for sid in shift_ids:
            shift = self.assignable_shifts[sid]
            for slot in range(shift.role_count):
                slot_vars = [
                    slot_assignments[tid][sid][slot]
                    for tid in talent_ids
                    if slot in slot_assignments[tid].get(sid, {})
                ]
                fill_terms.extend(slot_vars)
        
        
        penalty_terms = []
        shifts_by_week: dict[date, list] = {}


        #contracted hours are weekly so penalties need to be calculated per week, not across the whole schedule.
        for sid in shift_ids:
            week_start = week_start_for_date(self.assignable_shifts[sid].start_time.date())
            shifts_by_week.setdefault(week_start, []).append(sid)
        


        # For each talent, convert contract hours and overworkthreshold hours to centihours since CP-SAT 
        # only works with integers.
        for tid in talent_ids:
            talent = self.availability[tid]
            contract_hours = int(talent.weeklyhours *SCALE)
            threshold = int(talent.weeklyhours *OVERWORK_THRESHOLD * SCALE)

            for week_start, week_sids in shifts_by_week.items():

                hour_terms = []
                for sid in week_sids:
                    if sid not in assigned.get(tid, {}):
                        continue
                    
                    #for each shift that  the talent is eligible for this week, create a term assigned[tid][sid] * centihours
                    # if the solver sets assigned[tid][sid] =1, then the term counts to the centihours, otherwise, 0 
                    centihours = int(shift_duration_hours(self.assignable_shifts[sid]) * SCALE)
                    hour_terms.append(assigned[tid][sid] * centihours)
                
                if not hour_terms:
                    continue

                max_possible = sum(
                    int(shift_duration_hours(self.assignable_shifts[sid]) * SCALE)
                    for sid in week_sids
                    if sid in assigned.get(tid, {})
                )

                total_worked = model.new_int_var(0, max_possible , f"total_hours_for_talent{tid}_in_week_{week_start}")
                model.add(total_worked == sum(hour_terms))


                #shortfall is the number of hours below contract hours that a talent works in a week and its values are 
                #between 0 and contract hours
                #shortfall is used by the solver to check how far from filling the gap of contract hours a talent is, and used 
                #to incentivize the solver to either close the gap or stop choosing this talent.

                shortfall = model.new_int_var(0, contract_hours, f"shortfall_for_talent_{tid}_in_week_{week_start}")
                model.add_max_equality(shortfall, [contract_hours - total_worked, model.new_constant(0)])

                mild_excess = model.new_int_var(0, threshold - contract_hours, f"mild_excess_for_talent_{tid}in_week_{week_start}")
                capped = model.new_int_var(0, threshold, f"capped_excess_for_talent{tid}_in_week_{week_start}")
                model.add_min_equality(capped, [total_worked, model.new_constant(threshold)])
                model.add_max_equality(mild_excess, [capped - contract_hours, model.new_constant(0)])
 
                # --- steep_excess = max(0, total_var - threshold) ---
                steep_excess = model.new_int_var(0, max_possible + 1, f"steep_t{tid}_w{week_start}")
                model.add_max_equality(steep_excess, [total_worked - threshold, model.new_constant(0)])

                # ---- these are the terms that the solver uses to maximize the equation.
                penalty_terms.append(UNDERWORK_PENALTY    * shortfall)
                penalty_terms.append(MILD_OVERWORK_PENALTY  * mild_excess)
                penalty_terms.append(STEEP_OVERWORK_PENALTY * steep_excess)

                model.maximize(FILL_WEIGHT * sum(fill_terms) - sum(penalty_terms))


    def generate_schedule(self) -> list[assignment]:

        model = cp_model.CpModel()
        shift_ids = list(self.assignable_shifts.keys())
        talent_ids = list(self.availability.keys())

        slot_assignments = self._build_variables(model=model, shift_ids=shift_ids, talent_ids=talent_ids)
        assigned = self._convenience_methods(slot_assignments=slot_assignments, model=model)
        self._build_constraints(model=model, 
                                shift_ids=shift_ids, 
                                talent_ids=talent_ids, 
                                slot_assignments=slot_assignments, 
                                is_assigned=assigned)
        
        self._build_objective(model=model, 
                              assigned=assigned,
                              shift_ids=shift_ids,
                              talent_ids=talent_ids,
                              slot_assignments=slot_assignments)
        
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return []
        
        all_assignments = []
        for tid in talent_ids:
            for sid in shift_ids:
                if sid in assigned.get(tid, {}) and solver.value(assigned[tid][sid]) == 1:
                    all_assignments.append(assignment(
                        talent_id=tid,
                        shift_id=sid,
                        shift = self.assignable_shifts[sid]
                    ))
        
        return all_assignments



        
       
       