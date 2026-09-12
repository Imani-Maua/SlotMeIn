import pytest
from datetime import datetime, date, timedelta
from app.core.schedule.talents.schema import talentAvailability
from app.core.schedule.shifts.schema import shiftSpecification
from app.core.schedule.allocator.entities import assignment
from app.core.schedule.allocator.service import CSPScheduler
from app.core.utils.enums import Role
from collections import Counter
from tests.unit.utils import MON, TUE, _talent, _shift, _run

def test_fills_all_slots_when_enough_candidates():
    """Solver fills every slot when candidates are available."""
    availability = {1: _talent(1), 2: _talent(2), 3: _talent(3)}
    shifts = {"s1": _shift(1, role_count=2)}

    result = _run(availability, shifts)

    assert len(result) == 2
    assert all(a.shift_id == "s1" for a in result)
    assert len({a.talent_id for a in result}) == 2  # two distinct people


def test_does_not_overfill_slots():
    """Solver never assigns more people than role_count."""
    availability = {i: _talent(i) for i in range(1, 6)}
    shifts = {"s1": _shift(1, role_count=2)}

    result = _run(availability, shifts)

    shift_counts = Counter(a.shift_id for a in result)
    assert shift_counts.get("s1", 0) <= 2


def test_no_double_booking_same_day():
    """Each talent appears at most once per day even with two shifts available."""
    availability = {
        1: _talent(1, shifts=["am", "pm"]),
        2: _talent(2, shifts=["am", "pm"]),
    }
    shifts = {
        "am": _shift(1, role_count=1, shift_name="am", hour_start=9, hour_end=15),
        "pm": _shift(2, role_count=1, shift_name="pm", hour_start=15, hour_end=23),
    }

    result = _run(availability, shifts)

    talent_counts = Counter(a.talent_id for a in result)
    for tid, count in talent_counts.items():
        assert count == 1, f"Talent {tid} double-booked ({count} shifts on the same day)"


def test_role_mismatch_produces_no_assignment():
    """A server talent must not be assigned to a bartender shift."""
    availability = {1: _talent(1, role=Role.SERVER)}
    shifts = {"s1": _shift(1, role=Role.BARTENDER, role_count=1)}

    result = _run(availability, shifts)

    assert result == []


def test_unavailable_talent_not_assigned():
    """A talent with no availability window for the shift date is never assigned."""
    # talent only available on Tuesday, shift is on Monday
    availability = {1: _talent(1, dates=[TUE])}
    shifts = {"s1": _shift(1, d=MON, role_count=1)}

    result = _run(availability, shifts)

    assert result == []


def test_partial_fill_when_not_enough_candidates():
    """If only 1 talent is available for a 2-person slot, solver fills what it can."""
    availability = {1: _talent(1)}
    shifts = {"s1": _shift(1, role_count=2)}

    result = _run(availability, shifts)

    assert len(result) == 1
    assert result[0].talent_id == 1


def test_eleven_hour_rest_enforced_across_days():
    """If yesterday's shift ends at 23:00, talent cannot start today's shift at 09:00 (only 10h gap)."""
    yesterday_shift = _shift(99, d=MON, hour_start=15, hour_end=23)
    history = [assignment(talent_id=1, shift_id="hist", shift=yesterday_shift)]

    # Talent available Tuesday, but only 10h of rest since Monday's shift ended at 23:00
    availability = {
        1: _talent(1, dates=[TUE]),
        2: _talent(2, dates=[TUE]),
    }
    shifts = {"tue_am": _shift(1, d=TUE, role_count=1, hour_start=9, hour_end=17)}

    result = _run(availability, shifts, history=history)

    assigned_ids = {a.talent_id for a in result}
    assert 1 not in assigned_ids, "Talent 1 should be blocked by the 11-hour rest rule"
    assert 2 in assigned_ids, "Talent 2 (no history) should fill the slot"


def test_max_consecutive_days_enforced():
    """Talent with 6 days of history cannot be assigned on the 7th day."""
    # Build 6 days of history: Mon–Sat (2026-09-07 to 2026-09-12)
    base = date(2026, 9, 7)
    history = [
        assignment(
            talent_id=1,
            shift_id=f"hist_{i}",
            shift=shiftSpecification(
                template_id=i,
                start_time=datetime(2026, 9, 7 + i, 9),
                end_time=datetime(2026, 9, 7 + i, 17),
                shift_name="am",
                role_name=Role.SERVER,
                role_count=1,
            ),
        )
        for i in range(6)
    ]

    # Talent 1 has worked 6 consecutive days; talent 2 is fresh
    availability = {
        1: _talent(1, dates=[MON]),  # MON = 2026-09-14 (7th consecutive day)
        2: _talent(2, dates=[MON]),
    }
    shifts = {"s1": _shift(1, d=MON, role_count=1)}

    result = _run(availability, shifts, history=history)

    assigned_ids = {a.talent_id for a in result}
    assert 1 not in assigned_ids, "Talent 1 exceeded max consecutive days"
    assert 2 in assigned_ids
