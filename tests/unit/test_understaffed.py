from datetime import datetime, time
from app.core.schedule.allocator.service import UnderstaffedShifts
from app.core.schedule.allocator.entities import underStaffedShifts

def test_get_all_fully_staffed(make_shift, make_assignment):
    today = datetime.now().date()

    shift1 = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 30)),
        role_count=2
    )

    assignable_shifts = {"shift_1": shift1}

    assignment1 = make_assignment(talent_id=1, shift_id="shift_1", shift=shift1)
    assignment2 = make_assignment(talent_id=2, shift_id="shift_1", shift=shift1)

    validator = UnderstaffedShifts(conn=None, assignable_shifts=assignable_shifts, assigned_shifts=[assignment1, assignment2])

    result = validator.get_all()

    assert result == []


def test_unassigned_only(make_shift, make_assignment):
    today = datetime.now().date()

    shift1 = make_shift(
          start_time = datetime.combine(today, time(9, 0)),
          end_time = datetime.combine(today, time(15, 0)),
          role_count = 3
     )
    shift2 = make_shift(
          start_time = datetime.combine(today, time(15, 0)),
          end_time = datetime.combine(today, time(22, 0)),
          role_count = 3
     )
    
    assignable_shifts = {
        "shift1": shift1,
        "shift2": shift2
    }

    assignment1 = make_assignment(talent_id=1, shift_id="shift1", shift=shift1)
    assignment2 = make_assignment(talent_id=2, shift_id="shift1", shift=shift1)

    validator = UnderstaffedShifts(conn=None, assignable_shifts=assignable_shifts, assigned_shifts=[assignment1, assignment2])


    result = validator.unassigned_only()

    assert result == [shift2]


def test_get_all_partially_staffed(make_shift, make_assignment):
    today = datetime.now().date()

    shift1 = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 0)),
        role_count=3
    )

    assignable_shifts = {"shift1": shift1}

    assignment1 = make_assignment(
        talent_id=1,
        shift_id="shift1",
        shift=shift1
    )

    validator = UnderstaffedShifts(
        conn=None,
        assignable_shifts=assignable_shifts,
        assigned_shifts=[assignment1]
    )

    result = validator.get_all()

    assert len(result) == 1

    entry: underStaffedShifts = result[0]
    assert entry.shift_id == "shift1"
    assert entry.required == 3
    assert entry.assigned == 1
    assert entry.missing == 2


def test_get_all_mixed(make_shift, make_assignment):
    today = datetime.now().date()

    shift1 = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 0)),
        role_count=2
    )

    shift2 = make_shift(
        start_time=datetime.combine(today, time(17, 0)),
        end_time=datetime.combine(today, time(22, 0)),
        role_count=3
    )

    assignable_shifts = {
        "shift1": shift1,
        "shift2": shift2
    }

    # shift1 is fully staffed
    assignment1 = make_assignment(talent_id=1, shift_id="shift1", shift=shift1)
    assignment2 = make_assignment(talent_id=2, shift_id="shift1", shift=shift1)

    # shift2 is understaffed (only 1 of 3)
    assignment3 = make_assignment(talent_id=3, shift_id="shift2", shift=shift2)

    validator = UnderstaffedShifts(
        conn=None,
        assignable_shifts=assignable_shifts,
        assigned_shifts=[assignment1, assignment2, assignment3]
    )

    result = validator.get_all()

    assert len(result) == 1

    entry: underStaffedShifts = result[0]
    assert entry.shift_id == "shift2"
    assert entry.required == 3
    assert entry.assigned == 1
    assert entry.missing == 2