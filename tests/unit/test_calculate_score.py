import pytest
from datetime import datetime, timedelta, time
from app.core.schedule.allocator.engine.scheduler_scoring import computeScore

class TestCalculateScore:

    def test_higher_remaining_hours_gives_higher_score(
        self, base_shift, default_availability
    ):
        """Talent with more remaining weekly hours should score higher."""
        availability = {
            1: default_availability(1, weeklyhours=40),
            2: default_availability(2, weeklyhours=20),
        }
        engine = computeScore(base_shift, availability, assignments=[], workload={1: 0.0, 2: 0.0})
        assert engine.calculate_score(1) > engine.calculate_score(2)
    
    def test_talent_with_more_hours_scheduled_scores_lower(
        self, base_shift, default_availability
    ):
        """A talent who has already exceeded their weekly hours scores below a fresh one."""
        availability = {
            1: default_availability(1, weeklyhours=40),
            2: default_availability(2, weeklyhours=40),
        }
        engine = computeScore(base_shift, availability, assignments=[], workload={1: 20.0, 2: 0.0})
        assert engine.calculate_score(1) < engine.calculate_score(2)
    

    def test_work_streak_reduces_score(
        self, base_shift, default_availability, make_shift, make_assignment, start_of_week
    ):
        """Working yesterday creates a streak that lowers the score."""
        availability = {1: default_availability(1), 2: default_availability(2)}
 
        yesterday = datetime.combine(start_of_week - timedelta(days=1), time(9,0))
        yesterday_shift = make_shift(yesterday, yesterday + timedelta(hours=8))
        worked_yesterday = [make_assignment(1, shift_id=10, shift=yesterday_shift)]
 
        score_with_streak = computeScore(base_shift, availability, worked_yesterday, workload={1: 8.0} ).calculate_score(1)
        score_no_streak = computeScore(base_shift, availability, [], workload={2: 0.0} ).calculate_score(2)
 
        assert score_with_streak < score_no_streak
    
    
    def test_no_streak_returns_zero_penalty(
        self, base_shift, default_availability
    ):
        """work_streak=0 → streak score is 0.0 (neutral, no penalty, no bonus)."""
        availability = {1: default_availability(1)}
        score = computeScore(
            base_shift, availability, assignments=[], workload={1: 0.0}
        ).calculate_score(1)
 
        assert score == pytest.approx(40, abs=0.01)


    @pytest.mark.parametrize("days_worked, expected_streak_penalty", [
        (1, -2.0),   # tier 1–2 days
        (2, -2.0),   # tier 1–2 days (upper boundary)
        (3, -5.0),   # tier 3–4 days
        (4, -5.0),   # tier 3–4 days (upper boundary)
        (5, -10.0),  # tier 5–6 days
        (6, -10.0),  # tier 5–6 days (upper boundary)
    ])

    def test_streak_tier_penalties(
        self, days_worked, expected_streak_penalty,
        base_shift, default_availability, make_shift, make_assignment, start_of_week
    ):
        """Each streak tier returns the correct flat penalty."""
        availability = {1: default_availability(1)}
        assignments = []
        for days_ago in range(1, days_worked + 1):
            day = datetime.combine(start_of_week - timedelta(days=days_ago), time(9,0))
            shift = make_shift(day, day + timedelta(hours=8))
            assignments.append(make_assignment(1, shift_id=days_ago, shift=shift))
 
        score = computeScore(
            base_shift,  availability, assignments, workload={1: 0.0}
        ).calculate_score(1)
 
        # hours_balance=40, rest_gap=0
        assert score == pytest.approx(40 + expected_streak_penalty, abs=0.01)

    def test_streak_breaks_on_first_rest_day(
            self, base_shift, default_availability, 
            make_shift, make_assignment, start_of_week):
        """
        A gap in working days stops the streak count immediately.
        Talent worked days-ago 1 and 3 but NOT day 2 — streak must be 1 (tier: -2),
        not 2, because day 2 is a gap that breaks the loop.
        """
        availability = {1: default_availability(1)}
        assignments = []
        for days_ago in [1, 3]:   # gap at day 2
            day = datetime.combine(start_of_week - timedelta(days=days_ago), time(9,0))
            shift = make_shift(day, day + timedelta(hours=8))
            assignments.append(make_assignment(1, shift_id=days_ago, shift=shift))
 
        score = computeScore(base_shift, availability, assignments, workload={1: 0.0}).calculate_score(1)
 
       
        assert score == pytest.approx(40 - 2, abs=0.01)
    def test_assignments_older_than_6_days_ignored(
        self, base_shift, default_availability, make_shift, make_assignment, start_of_week
    ):
        """A shift 7 days ago is outside the look-back window and must not affect streaks."""
        availability = {1: default_availability(1)}

        old_day = datetime.combine(start_of_week - timedelta(days=7), time(9,0))
        old_shift = make_shift(old_day, old_day + timedelta(hours=8))
        old_assignment = [make_assignment(1, shift_id=77, shift=old_shift)]
 
        score_with_old = computeScore(
            base_shift, availability, old_assignment, workload={1: 0.0}
        ).calculate_score(1)
        score_clean = computeScore(
            base_shift, availability, [], workload={1: 0.0}
        ).calculate_score(1)
 
        assert score_with_old == pytest.approx(score_clean, abs=0.01)
    
    def test_less_than_11h_rest_incurs_penalty(
        self, default_availability, make_shift, make_assignment, start_of_week
    ):
        """< 11 h between yesterday's end and today's start → -5 rest-gap penalty.

        Setup: target shift starts Sunday at 09:00.
               yesterday's shift (Saturday) ends at 23:00 → only 10 h of rest.
        """
        availability = {1: default_availability(1)}

        target_shift_start = datetime.combine(start_of_week, time(9, 0))
        target_shift = make_shift(target_shift_start, target_shift_start + timedelta(hours=8))

        # Saturday: shift ends at 23:00 — only 10 hours before Sunday 09:00
        yesterday_date = start_of_week - timedelta(days=1)
        yesterday_shift_end = datetime.combine(yesterday_date, time(23, 0))
        yesterday_shift_start = yesterday_shift_end - timedelta(hours=8)
        yesterday_shift = make_shift(yesterday_shift_start, yesterday_shift_end)
        assignments = [make_assignment(1, shift_id=50, shift=yesterday_shift)]

        score = computeScore(
            target_shift, availability, assignments, workload={1: 0.0}
        ).calculate_score(1)

        # hours_balance = 40.0, streak (1 day) = -2.0, rest_gap (<11h) = -5.0
        assert score == pytest.approx(40 - 2 - 5, abs=0.01)

    def test_sufficient_rest_returns_no_penalty(
        self, default_availability, make_shift, make_assignment, start_of_week
    ):
        """≥ 11 h between yesterday's end and today's start → no rest-gap penalty.

        Setup: target shift starts Sunday at 09:00.
               yesterday's shift (Saturday) ends at 22:00 → exactly 11 h of rest.
        """
        availability = {1: default_availability(1)}

        target_shift_start = datetime.combine(start_of_week, time(9, 0))
        target_shift = make_shift(target_shift_start, target_shift_start + timedelta(hours=8))

        # Saturday: shift ends at 22:00 — exactly 11 hours before Sunday 09:00
        yesterday_date = start_of_week - timedelta(days=1)
        yesterday_shift_end = datetime.combine(yesterday_date, time(22, 0))
        yesterday_shift_start = yesterday_shift_end - timedelta(hours=8)
        yesterday_shift = make_shift(yesterday_shift_start, yesterday_shift_end)
        assignments = [make_assignment(1, shift_id=51, shift=yesterday_shift)]

        score = computeScore(
            target_shift, availability, assignments, workload={1: 0.0}
        ).calculate_score(1)

        # hours_balance = 40.0, streak (1 day) = -2.0, rest_gap (≥11h) = 0.0
        assert score == pytest.approx(40 - 2 - 0, abs=0.01)