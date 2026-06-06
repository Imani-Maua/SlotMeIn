from datetime import timedelta, date, datetime
from ortools.sat.python import cp_model
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.engine.utils import get_break_duration


def shift_duration_hours(shift: shiftSpecification) -> float:
    raw = (shift.end_time - shift.start_time).total_seconds/3600
    return raw - get_break_duration(shift.shift_name)


def talent_eligible_for_shift(talent:talentAvailability, shift: shiftSpecification) -> bool:
    if talent.role != shift.role_name:
        return False
    
    if shift.shift_name not in talent.shift_name:
        return False
    
    shift_date = shift.start_time.date()
    windows_for_day = talent.window.get(shift_date, [])

    if not windows_for_day:
        return False
    
    for (win_start, win_end) in windows_for_day:
        if isinstance(win_start, datetime) and isinstance(win_end, datetime):
            if win_start <= shift.start_time and shift.end_time <= win_end:
                return True

            else:
                start = datetime.combine(shift_date, win_start) if not isinstance(win_start, datetime) else win_start
                end = datetime.combine(shift_date, win_end) if not isinstance(win_end, datetime) else win_end
                if start <= shift.start_time and shift.end_time <= end:
                    return True
    return False


def find_last_shift_end(talent_id: int, on_date: date, history:list[assignment]):
    for assignment in history:
        if assignment.talent_id == talent_id and assignment.shift.start_time.date() == on_date:
            return assignment.shift.end_time
    return None

def days_worked_in_history(talent_id: int, history: list[assignment]) -> set:
    return {assign.shift.start_time.date() for assign in history if assign.talent_id == talent_id}

def week_start_for_date(dt: date) -> date:
    return dt - timedelta(days=(dt.weekday() + 1) % 7 )


def group_shifts_by_date(shift_ids: list[int], assignable_shifts:dict[int, shiftSpecification]):
    shifts_by_date: dict[date, list] = {}
    for sid in shift_ids:
        shift_date = assignable_shifts[sid].start_time.date()
        shifts_by_date.setdefault(shift_date, []).append(sid)
    
    return shifts_by_date

def is_talent_assigned(talent_ids: list[int], 
                       shift_ids: list[int], 
                       assignable_shifts: dict[int, shiftSpecification],
                       slot_assignments: dict,
                       model: cp_model.CpModel):
    assigned = {}
    for tid in talent_ids:
        assigned[tid] = {}
        for sid in shift_ids:
            shift = assignable_shifts[sid]
            talent_slots = [
                slot_assignments[tid][sid][slot]
                for slot in range(shift.role_count)
                if slot in slot_assignments.get(sid, {})
            ]
            if talent_slots:
                talent_works_shift = model.new_bool_var(f"assigned_talent{tid}_shift{sid}")
                model.add(sum(talent_slots) == talent_works_shift)
                assigned[tid][sid] = talent_works_shift
    return assigned

