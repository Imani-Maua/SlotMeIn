# SlotMeIn — Complete Technical Study


---

## Part 1 — What the system is

SlotMeIn is a restaurant staff scheduling system for a hotel restaurant in Budapest. It solves one problem: given a pool of staff with different roles, contracted hours, and availability constraints, produce a legal weekly schedule that fills every shift slot optimally.

The system has two distinct intellectual contributions:

1. **A constraint-programming scheduler** — replaces a greedy algorithm, uses Google OR-Tools CP-SAT to produce optimal schedules under hard labour law constraints and a multi-objective function grounded in real wage data.

2. **A machine learning tier predictor** — predicts whether a given day will be HIGH, MEDIUM, or LOW demand, based on hotel occupancy and weather signals, so the scheduler knows how many staff to put on each shift.

The thesis narrative is: greedy → CP-SAT → ML integration. Each step solves a problem the previous step couldn't.

---

## Part 2 — The technology stack

```
Frontend (React)
      ↓ HTTP
FastAPI (Python)         ← your API layer
      ↓
Redis Streams            ← job queue (schedule generation is async)
      ↓
Worker process           ← picks up jobs, runs the scheduler
      ↓
PostgreSQL               ← stores talents, schedules, constraints
      ↓
OR-Tools CP-SAT          ← solves the scheduling optimisation problem
      ↓
ML models (.pkl)         ← predicts staffing tier from occupancy + weather
```

**Why async?** Schedule generation can take up to 30 seconds (CP-SAT solving). If the API waited synchronously, the HTTP request would time out. Instead, the API publishes a job to Redis and immediately returns a `job_id`. The frontend polls `/jobs/{job_id}` or listens to a Server-Sent Events stream (`/events/{job_id}`) until the worker finishes and marks the job done.

---

## Part 3 — How a schedule is generated, end to end

When the manager clicks "Generate Schedule" on the frontend:

**Step 1 — Request lands at the API**
```
POST /generate
{ "start_date": "2024-10-13", "occupancy_pct": 0.85 }
```

**Step 2 — Route publishes to Redis**
`ScheduleJobQueue.publish(start_date, occupancy_pct)` pushes a message onto the `schedule:jobs` Redis stream and returns a `job_id`. The API responds immediately with `{ "job_id": "...", "status": "pending" }`.

**Step 3 — Worker picks up the job**
A separate process runs a loop consuming from `schedule:jobs`. It calls `process_job()` which calls `SchedulingService.generate(start_date, occupancy_pct)`.

**Step 4 — Shift slots are built**
`ShiftSlotBuilder` does two things:
- Loads all shift periods and templates from the database (e.g. Morning AM 06:00–16:00, 4 Server slots)
- For each day in the week, determines how many staff are needed per role per shift — either from the ML model (if `occupancy_pct` is provided) or from the day-of-week fallback

**Step 5 — Talents are loaded**
`TalentService` loads all active staff from the database, preprocesses their availability and constraints, and assembles them into `talentAvailability` objects the scheduler can reason about.

**Step 6 — CP-SAT solves**
`CSPScheduler` builds a constraint-programming model, adds five constraint types, defines the objective function, and calls the solver. The solver returns a set of `assignment` objects (talent → shift slot).

**Step 7 — Result is saved and returned**
The worker saves the schedule as a draft in PostgreSQL, marks the job done in Redis, and the frontend receives the schedule via the SSE stream.

---

## Part 4 — The greedy algorithm (the baseline)

Before CP-SAT, the scheduler used a greedy algorithm. Greedy means: go through shifts one by one, for each shift pick the best available talent right now, assign them, move on. Never look back.

The greedy approach has a fundamental flaw: **decisions are locally optimal but globally suboptimal.** If you assign your only available runner to Monday's morning shift because that's the first shift processed, and it turns out Monday evening desperately needed that runner, you have no way to undo the decision. The greedy algorithm has no concept of the full week — it is blind to future consequences of current choices.

CP-SAT solves this by considering the entire week simultaneously and finding the globally optimal assignment.

Both algorithms are preserved in the codebase. The thesis uses the greedy as the baseline to show CP-SAT's improvement.

---

## Part 5 — CP-SAT: what it is

CP-SAT stands for Constraint Programming — Satisfiability. It is a solver from Google's OR-Tools library. You give it:
- **Variables** — decisions to be made (integers or booleans)
- **Constraints** — rules those variables must satisfy
- **Objective** — a function to maximise or minimise

The solver searches the space of all possible variable assignments and finds the one that satisfies all constraints while maximising the objective. It uses a combination of SAT solving, linear programming relaxation, and backtracking search — but you don't need to understand the internals. What matters is: it finds the globally optimal solution, not just a locally good one.

**One critical fact:** CP-SAT only works with integers. All continuous values (hours, weights) are multiplied by 100 (called `SCALE`) before entering the model. So "4.5 hours" becomes 450 centihours internally.

---

## Part 6 — CP-SAT: the decision variables

The fundamental question the solver must answer is: **which talent fills which slot on which shift?**

For every combination of (talent, shift, slot), the solver creates a boolean variable:

```python
slot_assignments[tid][sid][slot] ∈ {0, 1}
# 1 = talent tid fills slot number `slot` in shift sid
# 0 = they don't
```

If a shift needs 4 servers, it has slots 0, 1, 2, 3. Each slot can be filled by at most one talent. Each talent can fill at most one slot per shift.

A convenience variable `assigned[tid][sid]` is derived — it equals 1 if the talent is assigned to the shift at all (in any slot). This makes the objective function cleaner.

**Important:** variables are only created if the talent is eligible for the shift. `talent_eligible_for_shift()` checks the talent's declared availability window before creating a variable. A part-time employee with a Tuesday–Thursday window simply has no variables for Monday or Friday — the solver cannot assign them there, no matter how many slots are open.

---

## Part 7 — CP-SAT: the five constraints

**Constraint 1 — Each slot filled by at most one talent**
Two people cannot share the same slot. `sum(slot_vars for slot) <= 1`.

**Constraint 2 — Each talent fills at most one slot per shift**
A talent can only show up once per shift. Even if three slots are open, they can only take one.

**Constraint 3 — At most one shift per talent per day**
A talent cannot work morning AND evening on the same day.

**Constraint 4 — Minimum 11 hours rest between days**
EU Working Time Directive requirement. If a talent finishes their evening shift at 23:59 and the next morning shift starts at 06:00, that is only 6 hours rest — illegal. The solver checks previous shift end times (from both the current week being solved AND historical assignments loaded from the database) and blocks any assignment that would violate the 11-hour rule.

**Constraint 5 — Maximum 6 consecutive working days**
Another WTD requirement. The solver tracks a rolling 7-day window. It counts days already worked in history and limits additional solver-assigned days so the total never exceeds 6.

---

## Part 8 — CP-SAT: the objective function

The solver maximises:

```
FILL_WEIGHT × Σ(fill_terms)
+ CONSTRAINED_FILL_BONUS × Σ(constrained_bonus_terms)
- Σ(penalty_terms)
```

The penalty terms are computed per talent per week, in centihours:

```
penalty = UNDERWORK_PENALTY × shortfall
        + MILD_OVERWORK_PENALTY × mild_excess
        + STEEP_OVERWORK_PENALTY × steep_excess
```

Where:
- `shortfall` = hours below contracted hours (0 if they worked their full contract)
- `mild_excess` = hours between contracted hours and 115% of contracted hours (acceptable overwork band)
- `steep_excess` = hours above 115% of contracted hours (welfare-concerning overwork)

**The five constants and their rationale:**

| Constant | Value | Why |
|----------|-------|-----|
| `FILL_WEIGHT` | 200 | An unfilled slot risks ~120,000–200,000 HUF of revenue per service — approximately 18× the labour cost of the same shift. Filling slots must dominate all other concerns. |
| `STEEP_OVERWORK_PENALTY` | 100 | Financially, the overtime premium is 0.5× base hourly. The weight is set to 2× the financial value, embedding a 2.5× welfare premium for burnout and turnover costs not captured in payroll. |
| `UNDERWORK_PENALTY` | 80 | Paying for hours where no work is produced. Financially this should be penalised 2× more than overwork premium. The weights invert this deliberately — welfare of overworked staff is treated as more important than financial waste of underworked hours. |
| `CONSTRAINED_FILL_BONUS` | 50 | Part-time employees (30hrs/week, `constraint=True`). Without the bonus, the solver under-uses them because their narrower availability and smaller contract create less natural pressure. The bonus corrects this systematic bias. Part-time staff are also cheaper per hour, so preferring them is financially efficient. |
| `MILD_OVERWORK_PENALTY` | 20 | Tables stay late, colleagues call in sick. This is operational noise in hospitality, barely discouraged. The 1:5 ratio with steep overwork (20:100) marks these as categorically different. |

**The threshold `OVERWORK_THRESHOLD = 1.15`:**
For a 40-hour contract: 1.15 × 40 = 46 hours. That is roughly one additional half-day shift — the natural unit of covering an absent colleague. It also sits safely below the EU Working Time Directive's 48-hour maximum (which is 1.20× for a 40-hour contract).

---

## Part 9 — How the staffing level is determined

Before the CP-SAT solver runs, the system needs to know *how many* slots exist per role per shift. This is `role_count` — the number of people needed.

**Old approach (day-of-week only):**
```python
"low": ["Monday", "Tuesday"],
"med": ["Wednesday", "Thursday"],
"high": ["Friday", "Saturday", "Sunday"]
```

Every Monday is treated the same regardless of whether the hotel is 10% or 90% occupied that week. This is why the before-screenshots show identical schedules across consecutive weeks.

**New approach (ML-predicted tier):**
The ML model predicts the tier (HIGH / MEDIUM / LOW) for each shift on each date using hotel occupancy, weather, season, and day of week as features. The tier then maps to a role count:

```python
Role.SERVER: {"low": 2, "med": 3, "high": 4}
Role.RUNNER: {"low": 1, "med": 2, "high": 3}
# etc.
```

A week where the hotel is 85% occupied gets different slot counts than a week where it is 20% occupied — even if both weeks contain the same days of the week. That difference is the thesis contribution.

---

## Part 10 — The demand tier problem

The ML model predicts one of three demand tiers — HIGH, MEDIUM, LOW — for each shift (morning, afternoon) on each day.

**Why three tiers?** The staffing configuration maps tiers to headcounts. Three tiers gives you enough granularity to distinguish busy from quiet from medium without over-complicating the prediction task. More tiers = harder classification problem = worse model.

**Morning tier:** Almost entirely driven by hotel occupancy. Hotel guests eat breakfast. If the hotel is 85% full, breakfast will be busy. The scoring rule uses thresholds: ≤35% → LOW, 36–65% → MEDIUM, >65% → HIGH, with hard overrides for Christmas, New Year's Eve, and New Year's Day.

**Afternoon tier:** More complex. Driven by a combination of occupancy, day of week, season, temperature, and special day status. Lunch and dinner guests are not just hotel guests — they are walk-ins, locals, tourists. A hot summer Friday is busy even with low hotel occupancy.

---

## Part 11 — The simulation: why it was needed

To train a machine learning model, you need labelled examples — (features, correct answer) pairs. The correct answer here is the tier label for each (date, shift).

The restaurant's real data covers December 2023 to April 2026 — roughly 840 dates. For a tier classifier, this is very thin. ML models need thousands of examples to generalise.

The solution: **simulate training data** using the Kaggle City Hotel dataset (2015–2017, ~806 days). The City Hotel is a real hotel with real occupancy patterns, real weather data, and real seasonal structure. We apply the same tier-scoring rules to this simulated data that we apply to the real restaurant data, producing labelled (features, tier) pairs.

The ML model trains on this simulated data. The test set is the real restaurant data. This is a **sim-to-real transfer** setup — a known methodology in robotics and reinforcement learning, less common in business analytics, which is part of what makes it interesting as a thesis contribution.

---

## Part 12 — The simulation: five-stage evolution

The simulation was not written once. It went through five iterations as we grounded each parameter in real data. The full log is in `thesis/simulation_design_log.md`. The summary:

**Stage 1 — Invented parameters.** Cover rates and weather made up from intuition.

**Stage 2 — Empirically grounded cover rates.** Computed monthly dinner cover rates from the real restaurant's covers data. Applied seasonal means where individual months had too few observations.

**Stage 3 — December ramp.** Observed that December is not uniformly busy — it ramps up toward Christmas. Separated early/late December using the real data.

**Stage 4 — Thin-month substitution.** April (n=8) and May (n=7) had too few observations for reliable individual estimates (95% CIs spanning ±0.20). Substituted with the spring season mean (0.43) from the combined March+April+May data.

**Stage 5 — Weather from Resort Hotel's actual climate data.** Replaced invented temperature ranges with the monthly mean/min/max from the Resort Hotel's location.

Each stage made the simulation more faithful to the real restaurant's operating environment.

---

## Part 13 — The ML models: seven training runs

All runs are logged in `thesis/model_training_log.md` and `thesis/strategy_log.md`. The summary of what we learned:

**Run 1** — Temporal 70/15/15 split on simulation data. Val and test windows fell entirely in summer. Afternoon tier is always HIGH in summer → 100% test accuracy on afternoon. Not a real result. Abandoned.

**Run 2** — City Hotel simulation as val set, 24-config regularisation sweep. Found the val→test gap on afternoon was distribution shift (City Hotel ≠ real restaurant), not overfitting. Best afternoon: LightGBM val 98.7%, test 89.9%.

**Run 3** — Resort Hotel only, season-stratified val split (15% of dates from each season). This fixed the summer-only val problem. Afternoon LightGBM: val 97.5%, test 87.7%. The ~10% val→test gap confirmed as structural distribution shift across all models and configurations.

**Run 4** — Within-month cover rate ramps computed per month. No effect. The ramps computed a new column that was never used in tier labels or features. Identified the lesson: within-month patterns must enter as a direct feature.

**Run 5** — Added `day_of_month` as a feature. It had 10% importance in afternoon (the model learned it) but zero improvement on test accuracy (still 87.7%). The within-month pattern the simulation encoded doesn't match the real restaurant's within-month pattern. Feature adds noise at generalisation time.

**Run 6** — Dropped `is_special_day` from morning (importance 0.000 — pure noise for breakfast demand). Zero impact on XGBoost and LightGBM test accuracy. Confirmed the two shifts need separate feature sets.

**Run 7 — FINAL** — Dropped `day_of_month`, `is_weekend`, `temp_max` from both shifts.
- `day_of_month`: high importance, zero test benefit — simulation-specific pattern
- `is_weekend`: near-zero importance (redundant with `day_of_week`)
- `temp_max`: always exactly `temp_mean + 3` in the simulation — perfectly collinear, contains no new information

Result: Afternoon overfitting halved (3.3% → 1.7%) at zero cost to test accuracy.

**Final models:**

| Shift | Model | Train | Val | Test | Gap |
|-------|-------|-------|-----|------|-----|
| Morning | XGBoost | 99.9% | 99.2% | 99.3% | +0.7% |
| Afternoon | LightGBM | 100.0% | 98.3% | 87.7% | +1.7% |

---

## Part 14 — Distribution shift: the honest ceiling

The afternoon model hits 87.7% test accuracy across every run, every model, every regularisation configuration. This is not a tuning problem. It is **distribution shift** — the simulation's afternoon feature distributions differ structurally from the real restaurant's.

Why? The afternoon tier is driven by multiple signals (occupancy, day of week, season, temperature, special day). The simulation approximates these signals from a Portuguese resort. The real restaurant is in Budapest. The mapping from features to tier labels is not identical.

The morning model has no such problem (99.3% test) because morning is dominated by a single signal — hotel occupancy (importance 75%). The simulation and the real restaurant use the same occupancy records, so there is no distribution shift.

The ~10% afternoon gap is a known limitation, documented and explained. It is not embarrassing — it is a finding. You ran 24 regularisation configurations and 7 training runs and confirmed the gap is irreducible given the simulation. That is methodological rigour.

---

## Part 15 — The inference wrapper

`app/core/schedule/ml/tier_predictor.py`

This is the bridge between the ML models and the scheduler. It loads all model artefacts once at startup (expensive — loading pickle files) and keeps them in memory. Every subsequent prediction call is fast — just feature construction and a model forward pass.

```python
predict_tier(dt, occupancy_pct, shift, temp_mean=None) → "high" | "med" | "low"
```

**Feature construction from inputs:**
- `occupancy_pct` → passed directly
- `day_of_week` → `dt.weekday()` (0=Monday, 6=Sunday)
- `is_weekend` → `weekday >= 5`
- `is_special_day` → True if Dec 25, Dec 31, or Jan 1
- `temp_mean` → passed directly, or defaults to Budapest seasonal average if None
- `temp_max` → `temp_mean + 3.0` (the simulation's fixed relationship)
- `season_*` → one-hot encoded from the month

The column subscript `pd.DataFrame([row])[arts["features"]]` enforces the exact column order the model was trained on. Without this, columns could arrive in dict-insertion order and silently produce wrong predictions.

**The normalisation step:** The label encoder returns `"medium"` but the staffing service uses `"med"`. The `normalize_staffing` dict maps between the two vocabularies at the boundary.

**Temperature defaults (Budapest, °C):**
- Spring (Mar–May): 12.0
- Summer (Jun–Aug): 22.0
- Autumn (Sep–Nov): 10.0
- Winter (Dec–Feb): −2.0

If `temp_mean` is not supplied, the system falls back to these — meaning the scheduler can work without a weather API for the thesis demo.

---

## Part 16 — How the integration works end to end

When `ShiftSlotBuilder` is initialised with `occupancy_pct`:

1. `_build_week_spec()` iterates over every day in the week
2. For each day, it iterates over every shift period
3. For each period, `_ml_shift_type()` checks the period's start time — before noon → `"morning"` model, after noon → `"afternoon"` model
4. `predict_tier()` is called → returns `"high"`, `"med"`, or `"low"`
5. These are collected into `tier_override = {period_id: tier}`
6. `apply_staffing_to_periods(tier_override=tier_override)` maps each period's tier to a role count using `staffing_configuration()`
7. The role counts become `role_count` on each `shiftSpecification`
8. CP-SAT receives these slot counts and fills them optimally

A high-occupancy week (0.85) produces more slots per role per shift than a low-occupancy week (0.20) — even on the same day of the week. This is the before/after difference visible in the schedules.

---

## Part 17 — The wage data and why it matters for the objective weights

All five CP-SAT objective constants are grounded in real wage records from the restaurant. The full table is in `thesis/objective_weights.md`.

**Hotel monthly revenue: ~21.9M HUF** — derived independently from each role's service charge percentage, all consistent with each other. This cross-validation confirms the wage figures are internally valid.

**The 2:1 financial ratio:** For any role, the cost of underwork (paying for nothing) is exactly 2× the overtime premium (the extra 50% above base for hours above contract). This holds regardless of base salary because the ratio is structural (100% vs 50%). If the scheduler were purely cost-minimising, it should penalise underwork 2× more than overwork.

**The welfare premium:** The implemented weights invert this ratio:
```
Financial says:  UNDERWORK : OVERWORK_PREMIUM = 2.0 : 1.0
Implemented:     UNDERWORK : OVERWORK_PREMIUM = 0.8 : 1.0  (80 vs 100)
Welfare premium: 2.0 / 0.8 = 2.5×
```

The scheduler treats steep overwork as 2.5× more harmful than pure financial analysis would suggest. This captures burnout, turnover, and WTD compliance costs that do not appear in payroll records.

---

## Part 18 — What is defensible vs what needs care

**Fully defensible:**
- Objective weight ratios (wage data + financial derivation)
- OVERWORK_THRESHOLD = 1.15 (46 hrs for 40hr contract, below WTD 48hr cap)
- MIN_REST_HOURS = 11 (EU WTD Article 3)
- MAX_CONSECUTIVE_DAYS = 6 (EU WTD Article 5)
- Morning model accuracy (99.3% — no distribution shift)
- Season-stratified val split design
- Feature ablation methodology

**Defensible with caveats:**
- Afternoon 87.7% test accuracy — distribution shift, not model failure. Explain clearly.
- Revenue at risk estimate (120k–200k HUF) — from manager conversation, cite it as such
- Welfare premium of exactly 2.5× — a design choice, not a derived target. Sensitivity analysis will show the schedule is stable under ±20% weight variation

**Explicitly flagged as assumptions:**
- Occupancy tier thresholds (35%/65%) — unvalidated against observed morning operational data
- Morning tier scoring circularity — model feature importances confirm the design assumption but do not independently validate it

---

## Part 19 — Questions for the professor (Friday 2026-10-10)

Full list in `thesis/professor_discussion.md`. The ten questions cover:

1. Is ~10% afternoon distribution shift acceptable?
2. Is sim-to-real training methodologically sound?
3. Is val-based model selection sufficient?
4. Is season-stratified split valid for non-autocorrelated simulation data?
5. Is 2.5% remaining afternoon overfitting worth addressing further?
6. How should April/May mismatch be reported?
7. Is morning tier circularity acceptable?
8. How much greedy vs CP-SAT comparison is needed?
9. Are the objective weight ratios empirically defensible?
10. What constitutes a meaningful "after" for the ML integration?

---

## Part 20 — What is left before writing

- [ ] Generate before/after schedule screenshots (one run at 0.20 occupancy, one at 0.85, same week)
- [ ] Sensitivity analysis: vary each objective weight ±20%, show schedule output is stable
- [ ] Per-month error analysis on afternoon test set (does Apr/May drive the 10% gap?)
- [ ] Professor meeting (Friday 2026-10-10) — use `thesis/professor_discussion.md`

Everything else is writing.

---

## Part 21 — System invariants

An invariant is a guarantee the system makes regardless of inputs. These are the hard contracts the scheduler enforces — if any of them break, the schedule is wrong by definition.

### Scheduling invariants (enforced by CP-SAT constraints)

**I1 — At most one talent per slot.**
No two people can occupy the same shift slot. A slot is a `(period_id, date, role, template_id)` tuple. The solver creates one binary variable per `(slot, talent)` pair and constrains `sum(vars for slot) ≤ 1`. This makes double-booking structurally impossible.

**I2 — At most one slot per talent per shift.**
Even if a period has three open Server slots, a single talent can fill only one. Prevents the solver from counting the same person twice in the same service.

**I3 — At most one shift per talent per day.**
A talent cannot be assigned to both morning and evening on the same date. The solver sums all slot variables across shifts on the same day and constrains the sum to ≤ 1.

**I4 — Minimum 11 hours rest between consecutive shifts.**
EU Working Time Directive (2003/88/EC), Article 3. If a talent's last assigned end time on day D is `T`, they cannot receive an assignment on day D+1 whose start time is before `T + 11 hours`. The solver loads historical assignments from the database to enforce this across week boundaries — a Sunday night shift in week N is checked against Monday morning in week N+1.

**I5 — Maximum 6 consecutive working days.**
EU Working Time Directive, Article 5. The solver counts days already worked in the 6 days preceding the schedule week (from historical data) and constrains additional solver-assigned days such that the rolling 7-day total never exceeds 6. A talent who worked Mon–Sat of the prior week cannot be assigned Sunday of the new week.

### Data and interface invariants

**I6 — `occupancy_pct` is always 0.0–1.0 at the API boundary; always 0–100 when the ML model sees it.**
The API schema declares `occupancy_pct: float | None = None`. The `predict_tier` function multiplies by 100 before building the feature row. These are the only two representations — no other layer touches the value. This was a critical bug early in the integration: the model was receiving 0.85 and interpreting it as 0.85% occupancy.

**I7 — Tier is always one of `{"low", "med", "high"}`.**
The label encoder returns `"low"`, `"medium"`, or `"high"`. The `normalize_staffing` dict in `tier_predictor.py` maps `"medium" → "med"` so that `staffing_configuration()` receives a key it recognises. No other string can propagate. If an unknown label appears, `normalize_staffing[label]` raises `KeyError` rather than silently producing a wrong count.

**I8 — Every schedule covers exactly 7 days.**
`SchedulingService.generate()` computes `week = [start_date + timedelta(days=i) for i in range(7)]`. The week is always Monday through Sunday. If a start date is not a Monday, the schedule still generates — it just does not start on Monday, but it is still exactly 7 days.

**I9 — Inactive talents are never scheduled.**
`ShiftSlotBuilder` queries `Talent` with `is_active=True`. Inactive talents are excluded from the eligible pool before CP-SAT even runs. Their slots are never created, so they cannot appear in any output.

**I10 — Talents with an approved time-off request on a given date are excluded from that date.**
Request filtering runs during eligible talent selection, keyed on `req_date`. A talent with an approved holiday on Wednesday will have no slot variables created for Wednesday. The constraint is applied before the solver, not in the objective — it is a hard exclusion, not a soft penalty.

**I11 — Staffing role counts are non-negative integers.**
The `StaffingRule.count` column is `Integer` with the Pydantic update schema enforcing `ge=0`. The CP-SAT solver creates exactly `count` slot variables per role per period — a count of 0 means the solver does not create any variables for that role on that period, effectively removing the role from the schedule.

### Why invariants matter for the thesis

The scheduling literature distinguishes *hard constraints* (must not be violated) from *soft constraints* (penalised if violated). In SlotMeIn, I1–I5 are hard — the solver's constraint programming model makes violation mathematically impossible, not just unlikely. This is a key advantage of CP-SAT over heuristic or greedy methods: hard constraints are not approximations, they are enforced by the solver's propagation engine at every node of the search tree.

I6–I11 are application-level invariants enforced by the code structure rather than by the solver. They are documented here because breaking them produces silent wrong output rather than a solver infeasibility — the solver would just generate a schedule with wrong counts or wrong people, with no error raised.
