from datetime import datetime, timedelta, time
from conftest import make_asignment, make_context, make_shift
from app.core.schedule.allocator.engine.validators import consecutiveValidator
def test_consecutive_day_validator_under_limit(make_asignment:make_asignment, make_context:make_context, make_shift:make_shift):
    today = datetime.now().date()


    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 4)
    ]

    past_assignments = [
        make_asignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 4)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)

    assert consecutiveValidator().can_assign_shift(context=context) is True



def test_consecutive_day_validator_at_limit(make_asignment:make_asignment, make_context:make_context, make_shift:make_shift):
    

    today = datetime.now().date()

    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 6)
    ]

    past_assignments = [
        make_asignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 6)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is True



def test_consecutive_day_validator_beyond_limit(make_asignment:make_asignment, make_context:make_context, make_shift:make_shift):
    

    today = datetime.now().date()

    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 7)
    ]

    past_assignments = [
        make_asignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 7)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is False


def test_consecutive_day_validator_no_history(make_asignment:make_asignment, make_context:make_context, make_shift:make_shift):
    

    today = datetime.now().date()

    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 7)
    ]

    past_assignments = []

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is True






    
