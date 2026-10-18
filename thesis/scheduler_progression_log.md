# Scheduler Progression Log

---

## Stage 4 — CP-SAT + Historical Analysis (ML-Informed Staffing)

**Date:** 2026-10-07  
**Approach:** CP-SAT constraint solver (OR-Tools) with staffing levels driven by ML tier predictions trained on two years of historical booking data.

The tier model (XGBoost for AM, LightGBM for PM) predicts the expected service tier for each day — low, mid, or peak — based on occupancy, day-of-week, seasonality, and weather features. `StaffingService` maps predicted tiers to per-role headcounts that become the lower and upper bounds on the CP-SAT staffing constraints, replacing the previously hardcoded values.

**Key improvement over Stage 3:** The solver no longer targets the same fixed headcount every week. Staffing levels flex with predicted demand: a forecast peak weekend provisions more servers than a thin Tuesday, without any manager intervention.

**Result:** All roles fully staffed on every day; no understaffed slots. Staffing counts vary by day in line with the predicted tier.

![CP-SAT + Historical Schedule Grid](figures/scheduler/cpsat_historical_schedule.png)

---

## Stage 3 — CP-SAT (Constraint Programming)

**Date:** 2026-10-07  
**Approach:** OR-Tools CP-SAT solver with hard constraints — role eligibility, availability windows, shift overlap, and fixed minimum headcounts per role per shift.

The solver is given a set of Boolean decision variables — one per `(talent, shift_slot)` pair — and the following constraints:

1. A talent can only be assigned to a slot for which they are eligible (role match + availability window overlap).
2. No two assigned slots for the same talent can overlap in time.
3. For each `(shift_slot, role)` pair, the number of assigned talents must meet the required minimum.

OR-Tools then finds a feasible assignment that satisfies all constraints simultaneously.

**Key improvement over Stage 2 (Greedy):** The greedy algorithm assigns talents one at a time and has no lookahead — it can satisfy an early shift and leave no eligible talent available for a later shift. CP-SAT considers all assignments globally and backtracks, so it finds the schedule that works for every slot at once.

**Result:** Every role on every day fully covered. No understaffed shifts.

![CP-SAT Schedule Grid](figures/scheduler/cpsat_schedule.png)

---

## Stage 2 — Greedy Algorithm

**Date:** 2026-10-07  
**Approach:** Iterates over all `(shift_slot, role)` pairs in chronological order and greedily assigns the first eligible, available talent to each slot until the required headcount is met (or eligible talents are exhausted).

Eligibility checks: role match, availability window overlap, no existing time conflict for the talent.

**Limitation:** No lookahead. Talents consumed early in the week are unavailable for later slots that may have fewer substitutes. This produces schedules with understaffed days, particularly toward the end of the week, and does not recover from a locally-greedy bad choice.

**Result:** Some shifts understaffed, especially later in the week. Non-deterministic quality — outcome depends on the iteration order of talent records.

![Greedy Schedule Grid](figures/scheduler/greedy_schedule.png)

---

## Stage 1 — Excel (Manual)

**Date:** Pre-development  
**Approach:** Managers built weekly schedules by hand in a spreadsheet, applying role assignments manually based on availability communicated informally (text messages, verbal confirmation).

**Limitations:**
- No constraint enforcement — double-bookings, ineligible assignments, and missed minimum headcounts went undetected.
- No demand signal — staffing levels were based on manager intuition, not occupancy or historical data.
- Not reproducible — each schedule was a one-off artefact with no audit trail.
- O(n) manager time per schedule, proportional to team size.

**Result:** Functional but error-prone; served as the baseline that motivated the algorithmic work.

![Excel Schedule](figures/scheduler/excel_schedule.png)

---

## Architecture Notes

### Async pipeline (Stage 3+)

```
POST /schedule/generate
    → Redis stream (job_queue)
        → Worker process (cp_sat_allocator.solve())
            → result stored in Redis hash (JobResultStore)
                → client polls GET /schedule/job/{job_id}
                    → toast notification on status=done
```

### Key files

| File | Role |
|------|------|
| `app/core/schedule/allocator/service.py` | CP-SAT model definition and solve |
| `app/core/schedule/shifts/service.py` | Talent eligibility filter |
| `app/core/schedule/service.py` | Orchestrates solver, persists result, builds JSON response |
| `app/core/schedule/repo.py` | CRUD + `load_history()` for historical analysis |
| `app/redis/job_queue.py` | Redis stream producer/consumer |
| `src/pages/Schedule/Schedule.jsx` | Background polling `useEffect`, toast on completion |
| `src/pages/Schedule/DraftScheduleGrid.jsx` | Role-grouped grid, staffing counts, talent week panel |
