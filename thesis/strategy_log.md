
# Tier Model — Strategy Log

All approaches tried, in order. Each entry records the strategy, motivation, and outcome.

---

## Run 1 — Temporal 70/15/15 split
**Strategy:** Resort Hotel simulation only. Temporal split: first 70% of dates → train, next 15% → val, last 15% → test.  
**Motivation:** Standard time-series split to avoid data leakage.  
**Problem:** The val and test windows fell entirely in May–Sep 2017 — all summer. Afternoon tier is deterministically HIGH in summer, making the test trivially easy.  
**Result:** 100% test accuracy on afternoon. Not a real result.  
**Outcome:** Abandoned. Switched to cross-dataset evaluation.

---

## Run 2 — City Hotel as val, 24-config regularisation sweep
**Strategy:** Resort Hotel sim → train. City Hotel sim → val. Real hotel → test. Swept 24 regularisation configurations (max_depth, min_samples_leaf, reg_alpha, reg_lambda, min_child_weight, num_leaves, min_child_samples).  
**Motivation:** Fix the summer-only val problem. City Hotel provides full seasonal coverage. Sweep to eliminate overfitting.  
**Best result:**

| Shift | Model | Train | Val | Test | Gap |
|-------|-------|-------|-----|------|-----|
| Morning | XGBoost | 99.9% | — | — | — |
| Afternoon | LightGBM | 100% | 98.7% | 89.9% | +1.3% |

**Finding:** No configuration reduced the afternoon train→val gap below ~1%. Confirmed as distribution shift between resort and city hotel feature distributions — not overfitting. City Hotel val ≠ real restaurant.  
**Outcome:** Approach valid but City Hotel val is still a simulation. Moved to resort-only with stratified split.

---

## Run 3 — Resort only, season-stratified val
**Strategy:** Resort Hotel sim for both train and val. Instead of temporal split, sampled 15% of dates from each season independently for val → all 4 seasons represented.  
**Motivation:** Fix summer-only val without needing a second dataset.  
**Val breakdown:** Spring 28, Summer 37, Autumn 29, Winter 27 dates (121 total). Train: 685 dates.  
**Result:**

| Shift | Model | Train | Val | Test | Gap |
|-------|-------|-------|-----|------|-----|
| Morning | XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| Afternoon | LightGBM ★ | 100.0% | 97.5% | 87.7% | +2.5% |

**Finding:** Val now reflects realistic seasonal difficulty. Afternoon val→test gap (~10%) confirmed as structural distribution shift.  
**Outcome:** Solid baseline. Carried forward.

---

## Run 4 — Within-month cover rate ramps
**Strategy:** Derived early/late means per month from real covers data. Applied linear ramp within each month for all months with n≥7 in both halves (all except Apr, May). Stored as `dinner_cover_rate_base`.  
**Motivation:** Make simulation more faithful to within-month dynamics (e.g. October dropping sharply mid-month).  
**Result:** Identical to Run 3.  
**Finding:** The ramps computed `dinner_cover_rate_base` but this column was never used in tier label computation or model features. No effect on training data.  
**Outcome:** Abandoned. Identified that `day_of_month` must be added directly as a feature for within-month patterns to reach the model (Run 5).

---

## Run 5 — Add `day_of_month` as feature
**Strategy:** Same as Run 3 but added `day_of_month` (1–31) to both morning and afternoon feature sets. Gives the model direct access to within-month position.  
**Motivation:** Within-month patterns are real (e.g. September drops in second half). `day_of_month` is always known at prediction time.  
**Result:**

| Shift | Model | Train | Val | Test | Gap |
|-------|-------|-------|-----|------|-----|
| Morning | XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| Afternoon | LightGBM ★ | 100.0% | 96.7% | 87.7% | +3.3% |

**Finding:** `day_of_month` has 10% importance in afternoon — the model learned from it. But test accuracy unchanged (87.7%). Val dropped 0.8% (97.5% → 96.7%), meaning the feature added noise in cross-validation without helping generalisation. The within-month pattern in the simulation does not align with the real restaurant's within-month pattern.  
**Outcome:** Feature kept for now pending ablation. Afternoon gap widened slightly to 3.3%.

---

## Run 6 — Ablation: drop `is_special_day` from morning
**Strategy:** Remove `is_special_day` from morning feature set only. Afternoon unchanged.  
**Motivation:** Morning `is_special_day` importance = 0.000 in Run 5 — pure noise for morning tier.  
**Result (morning only):**

| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 99.7% | 99.2% | 95.7% | +0.5% |
| XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| LightGBM | 99.7% | 98.3% | 98.1% | +1.4% |

**Finding:** Zero impact on XGBoost and LightGBM. RF test improved 0.7% (95.0% → 95.7%). Feature confirmed as noise for morning — dropped.  
**Outcome:** Morning and afternoon now use separate feature sets.

### Current feature sets (Run 6)
- **Morning (9 features):** `occupancy_pct, day_of_week, day_of_month, is_weekend, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`
- **Afternoon (10 features):** `occupancy_pct, day_of_week, day_of_month, is_weekend, is_special_day, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`

---

## Current best models (Run 6)

| Shift | Model | Train | Val | Test | Train→Val | Val→Test |
|-------|-------|-------|-----|------|-----------|----------|
| Morning | XGBoost | 99.9% | 99.2% | 99.3% | +0.7% | −0.1% |
| Afternoon | LightGBM | 100.0% | 96.7% | 87.7% | +3.3% | −9.0% |

**Morning:** No meaningful overfitting. Val and test are effectively equal.  
**Afternoon:** Mild overfitting (3.3% train→val). Dominant issue is distribution shift (9% val→test). The ~87–88% test ceiling has persisted across all six runs.

---

---

## Run 7 — Ablation: drop `day_of_month`, `is_weekend`, `temp_max`
**Strategy:** Remove three features from both shifts simultaneously.  
**Motivation:**
- `day_of_month` — 10% importance in afternoon but zero test improvement; within-month pattern learned from simulation doesn't transfer to real data
- `is_weekend` — near-zero importance in both shifts (0.2–0.5%); redundant with `day_of_week`
- `temp_max` — perfectly collinear with `temp_mean` in simulation (always `temp_mean + 3`); redundant by construction

**Result:**

| Shift | Model | Train | Val | Test | Gap |
|-------|-------|-------|-----|------|-----|
| Morning | XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| Afternoon | LightGBM ★ | 100.0% | 98.3% | 87.7% | +1.7% |

**vs Run 6:**

| Shift | Val Δ | Test Δ | Gap Δ |
|-------|-------|--------|-------|
| Morning | 0.0% | 0.0% | 0.0% |
| Afternoon | +1.6% | 0.0% | −1.6% |

**Finding:** Morning unchanged — features were genuinely redundant. Afternoon overfitting nearly halved (3.3% → 1.7%) at zero cost to test accuracy. The three dropped features were causing the model to fit simulation-specific patterns that did not generalise.

### Final feature sets (Run 7)
- **Morning (6 features):** `occupancy_pct, day_of_week, temp_mean, season_Spring, season_Summer, season_Winter`
- **Afternoon (7 features):** `occupancy_pct, day_of_week, is_special_day, temp_mean, season_Spring, season_Summer, season_Winter`

### Feature importances (Run 7)
**Morning (XGBoost):** occupancy_pct 0.752 · temp_mean 0.130 · season_Winter 0.055 · season_Summer 0.033 · day_of_week 0.018 · season_Spring 0.012  
**Afternoon (LightGBM):** temp_mean 0.289 · day_of_week 0.274 · occupancy_pct 0.274 · is_special_day 0.085 · season_Spring 0.051 · season_Winter 0.023 · season_Summer 0.003

---

## Current best models (Run 7)

| Shift | Model | Train | Val | Test | Train→Val | Val→Test |
|-------|-------|-------|-----|------|-----------|----------|
| Morning | XGBoost | 99.9% | 99.2% | 99.3% | +0.7% | −0.1% |
| Afternoon | LightGBM | 100.0% | 98.3% | 87.7% | +1.7% | −10.6% |

**Morning:** No meaningful overfitting. Lean 6-feature model generalises cleanly.  
**Afternoon:** Overfitting reduced to 1.7%. Dominant issue remains distribution shift (val→test ~10.6%). Test ceiling of ~87–88% has held across all seven runs.

---

## Strategies pending / to explore

- [ ] K-fold cross-validation stratified by season — more robust val estimate than a single split
- [ ] Per-month error analysis on test set — isolate whether Apr/May drive the val→test gap

---

## Current scheduler state — "before" the ML integration

The CP-SAT solver is functional but blind to occupancy. Staffing levels (`role_count` per shift) come from a hardcoded day-of-week lookup in `app/core/schedule/staffing/service.py`. The ML tier models exist and are saved, but their output is not yet routed into the scheduler.

**Evidence — two consecutive October weeks produce identical schedules:**

![Week of Oct 11–17](figures/scheduler_static_week1_oct11.png)
![Week of Oct 18–24](figures/scheduler_static_week2_oct18.png)

Every role count is identical across both weeks. The solver is doing its job correctly (filling slots optimally given the staffing numbers it receives) — but the staffing numbers it receives never change.

**What the thesis integration must close:**

| Step | Component | Status |
|------|-----------|--------|
| 1 | Tier model inference wrapper | Done — `app/core/schedule/ml/tier_predictor.py` |
| 2 | Tier → `role_count` mapping in staffing service | Done — `apply_staffing_to_periods(tier_override=...)` |
| 3 | Source for `occupancy_pct` at prediction time | Done — passed in `POST /generate` body, threaded through Redis → worker → solver |
| 4 | Source for `temp_mean` at prediction time | Seasonal Budapest default in `tier_predictor.py`; optional override |
| 5 | End-to-end smoke test | Done — 72% occupancy, Oct 11–17 |

---

## "After" — ML-integrated schedule (72% occupancy, Oct 11–17)

Schedule generated with `occupancy_pct=0.72`. The ML tier predictor runs once per shift period per day, consuming occupancy + seasonal temperature + day-of-week. Staffing counts vary across the week based on predicted demand tier.

![72% occupancy — Oct 11–17](figures/scheduler_ml_72pct_oct11.png)

The variation is visible: Friday/Saturday push Leader and Server counts to their HIGH-tier values (3–4), while mid-week shifts hold at MED. This schedule was produced by the same CP-SAT solver as the "before" screenshots — the only change is that `role_count` now comes from the ML model rather than from the day-of-week lookup.
