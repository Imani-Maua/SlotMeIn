from datetime import datetime, timedelta, time
from app.core.schedule.allocator.engine.validators import consecutiveValidator, restValidator, dailyAssignmentValidator


# ---------------------------------------------------------------------------
#                       CONSECUTIVE DAYS VALIDATOR
# ---------------------------------------------------------------------------

def test_consecutive_day_validator_under_limit(make_assignment, make_context, make_shift):
    today = datetime.now().date()


    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 4)
    ]

    past_assignments = [
        make_assignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 4)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)

    assert consecutiveValidator().can_assign_shift(context=context) is True



def test_talent_working_five_days_can_still_be_assigned(make_assignment, make_context, make_shift):
    

    today = datetime.now().date()

    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 6)
    ]

    past_assignments = [
        make_assignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 6)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is True



def test_consecutive_day_validator_beyond_limit(make_assignment, make_context, make_shift):
    

    today = datetime.now().date()

    past_shifts = [
        make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(1, 7)
    ]

    past_assignments = [
        make_assignment(talent_id = 1, shift_id = i, shift = past_shifts[i-1] )
            for i in range(1, 7)
    ]

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is False


def test_consecutive_day_validator_no_history(make_context, make_shift):
    

    today = datetime.now().date()

    past_assignments = []

    shift_today = make_shift(
       start_time=datetime.combine(today , time(9, 0)),
       end_time=datetime.combine(today , time(17, 0)),
    )

    context = make_context(talent_id=1, shift = shift_today, assignments = past_assignments)


    assert consecutiveValidator().can_assign_shift(context=context) is True




# ---------------------------------------------------------------------------
#                       REST VALIDATOR
# ---------------------------------------------------------------------------


def test_rest_no_shift_yesterday(make_context, make_shift, make_assignment):
    
    today = datetime.now().date()
    shift_today = make_shift(
        start_time = datetime.combine(today, time(6, 0)),
        end_time = datetime.combine(today, time(15, 0))
    )


    past_shifts = [
         make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(17, 0)),

        )
        for i in range(2, 4)
    ]

    past_assignments = [
        make_assignment(talent_id= 1, shift_id= i, shift = shift)
        for i, shift in enumerate(past_shifts, start=1)
    ]

    context = make_context(talent_id=1, shift=shift_today, assignments = past_assignments)

    assert restValidator().can_assign_shift(context=context) is True

def test_rest_sufficient_rest_since_yesterday(make_context, make_shift, make_assignment):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time = datetime.combine(today, time(6, 0)),
        end_time = datetime.combine(today, time(15, 0))
    )


    past_shifts = [
         make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(9, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(15, 0)),

        )
        for i in range(1, 4)
    ]

    past_assignments = [
        make_assignment(talent_id= 1, shift_id= i, shift = shift)
        for i, shift in enumerate(past_shifts, start=1)
    ]

    context = make_context(talent_id=1, shift=shift_today, assignments = past_assignments)

    assert restValidator().can_assign_shift(context=context) is True


def test_rest_insufficient_rest(make_context, make_shift, make_assignment):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time = datetime.combine(today, time(6, 0)),
        end_time = datetime.combine(today, time(15, 0))
    )


    past_shifts = [
         make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(15, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(23, 0)),

        )
        for i in range(1, 4)
    ]

    past_assignments = [
        make_assignment(talent_id= 1, shift_id= i, shift = shift)
        for i, shift in enumerate(past_shifts, start=1)
    ]

    context = make_context(talent_id=1, shift=shift_today, assignments = past_assignments)

    assert restValidator().can_assign_shift(context=context) is False

def test_rest_exactly_11_hours(make_context, make_shift, make_assignment):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time = datetime.combine(today, time(6, 0)),
        end_time = datetime.combine(today, time(15, 0))
    )


    past_shifts = [
         make_shift(
            start_time=datetime.combine(today - timedelta(days=i), time(12, 0)),
            end_time=datetime.combine(today - timedelta(days=i), time(19, 0)),

        )
        for i in range(1, 4)
    ]

    past_assignments = [
        make_assignment(talent_id= 1, shift_id= i, shift = shift)
        for i, shift in enumerate(past_shifts, start=1)
    ]

    context = make_context(talent_id=1, shift=shift_today, assignments = past_assignments)

    assert restValidator().can_assign_shift(context=context) is True


def test_rest_pick_the_right_talent(make_context, make_assignment, make_shift):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time = datetime.combine(today, time(6, 0)),
        end_time = datetime.combine(today, time(15, 0))
    )

    talent1_yesterday = make_shift(
        start_time=datetime.combine(today - timedelta(days=1), time(6, 0)),
        end_time=datetime.combine(today - timedelta(days=1), time(15, 0))
    )

    # Talent 2 - insufficient rest, ended 11pm yesterday (7 hours)
    talent2_yesterday = make_shift(
        start_time=datetime.combine(today - timedelta(days=1), time(15, 0)),
        end_time=datetime.combine(today - timedelta(days=1), time(23, 0))
    )

    assignments = [
        make_assignment(talent_id=1, shift_id=1, shift=talent1_yesterday),
        make_assignment(talent_id=2, shift_id=2, shift=talent2_yesterday),
    ]

    context = make_context(talent_id=2, shift=shift_today, assignments = assignments)

    assert restValidator().can_assign_shift(context=context) is False



# ---------------------------------------------------------------------------
#                       DAILY ASSIGNMENT VALIDATOR
# ---------------------------------------------------------------------------

def test_daily_not_yet_assigned(make_context, make_shift):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 0))
    )

    context = make_context(talent_id=1, shift=shift_today, assignments=[])

    assert dailyAssignmentValidator().can_assign_shift(context=context) is True


def test_daily_already_assigned(make_context, make_shift):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 0))
    )

    context = make_context(talent_id=1, shift=shift_today, assignments=[])

    validator = dailyAssignmentValidator()
    validator.mark_assigned(context)

    assert validator.can_assign_shift(context=context) is False


def test_daily_different_talent_same_day(make_context, make_shift):
    today = datetime.now().date()
    shift_today = make_shift(
        start_time=datetime.combine(today, time(9, 0)),
        end_time=datetime.combine(today, time(17, 0))
    )

    context_talent1 = make_context(talent_id=1, shift=shift_today, assignments=[])
    context_talent2 = make_context(talent_id=2, shift=shift_today, assignments=[])

    validator = dailyAssignmentValidator()
    validator.mark_assigned(context_talent1)

    assert validator.can_assign_shift(context=context_talent2) is True