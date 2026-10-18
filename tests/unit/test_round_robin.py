from app.core.schedule.allocator.engine.scheduler_scoring import roundRobinPicker


def test_returns_none_for_empty_candidates():
    """An empty candidate list must return None — no crash, no guess."""
    picker = roundRobinPicker()

    result = picker.pickBestFit("server", [])

    assert result is None


def test_single_candidate_always_returned():
    """With only one candidate, every call must return that same talent."""
    picker = roundRobinPicker()
    candidates = [42]

    first_pick = picker.pickBestFit("server", candidates)
    second_pick = picker.pickBestFit("server", candidates)

    assert first_pick == 42
    assert second_pick == 42


def test_cycles_through_multiple_candidates_in_order():
    """Three candidates across four calls — must cycle back to the first after exhausting the list.

    Round-robin picks position 0 → 1 → 2 → 0 (wraps).
    """
    picker = roundRobinPicker()
    candidates = [1, 2, 3]

    first_pick  = picker.pickBestFit("server", candidates)
    second_pick = picker.pickBestFit("server", candidates)
    third_pick  = picker.pickBestFit("server", candidates)
    fourth_pick = picker.pickBestFit("server", candidates)   # must wrap back

    assert first_pick  == 1
    assert second_pick == 2
    assert third_pick  == 3
    assert fourth_pick == 1  # wrapped


def test_roles_have_independent_pointers():
    """Advancing the pointer for 'server' must not affect the pointer for 'bartender'.

    After two 'server' picks, 'bartender' should still start from position 0.
    """
    picker = roundRobinPicker()
    server_candidates    = [10, 20, 30]
    bartender_candidates = [40, 50, 60]

    picker.pickBestFit("server", server_candidates)   # pointer for server → 1
    picker.pickBestFit("server", server_candidates)   # pointer for server → 2

    # bartender pointer is untouched — should pick index 0
    bartender_first_pick = picker.pickBestFit("bartender", bartender_candidates)

    assert bartender_first_pick == 40
