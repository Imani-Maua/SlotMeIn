when # Professor Discussion — 2026-10-10 (Friday)

Questions to raise in progress meeting.

---

## 1. Distribution shift — is ~10% val→test gap acceptable?

Afternoon tier model hits a ceiling: val accuracy (resort sim) ~97–98%, real hotel test ~87–88% — a ~10% drop across every model and every regularisation configuration we tried. We ran a 24-config sweep and confirmed no regularisation closes this gap.

Our interpretation: the simulation generates afternoon feature distributions that differ structurally from the real restaurant's data. This is **distribution shift**, not overfitting.

**Questions:**
- Is this level of distribution shift acceptable in a thesis context, or does it need to be reduced further?
- How should we frame it in the write-up — as a known limitation, or as a finding in itself?
- Is there a standard way to quantify and report distribution shift between train and test populations (e.g. covariate shift metrics)?

---

## 2. Defensibility of simulation-based training

We have only ~1,676 real labelled rows (Dec 2023 – Apr 2026). To train a model we simulated ~806 days of Resort Hotel data (Kaggle) and used that as training. The simulation parameters (dinner cover rate, weather, occupancy) are empirically grounded from real covers data.

**Questions:**
- Is training on simulated data and testing on real data a methodologically sound approach for a thesis?
- Should we explicitly call this out as a **sim-to-real transfer** problem?
- Would an examiner push back on this, and if so, what is the strongest defence?

---

## 3. Model selection methodology

We select the best model per shift (morning/afternoon) by **val accuracy** — never touching the test set during selection. The test set is used only for final reporting.

- Morning best: XGBoost (val 99.2%, test 99.3%)
- Afternoon best: LightGBM (val 97.5%, test 87.7%)

**Questions:**
- Is val-based selection sufficient, or should we report confidence intervals / statistical tests on the test results?
- Given the small real test set (1,676 rows), is accuracy the right metric or should we be reporting F1 / balanced accuracy given any class imbalance?

---

## 4. Val set design — stratified vs temporal split

The original temporal split (last 15% of simulation dates) put the entire val window in summer — making afternoon trivially easy (always HIGH in summer). We fixed this with a **season-stratified split**: 15% of dates sampled from each season independently, so all four seasons appear in val.

**Questions:**
- Since simulation data has no temporal autocorrelation (each day is independently drawn), is random/stratified splitting valid? Or should we still respect temporal ordering?
- Is season-stratified the right stratification variable, or should we stratify on something else (e.g. tier distribution)?

---

## 5. Mild overfitting on afternoon — worth addressing further?

Afternoon shows small but real overfitting: LightGBM train→val gap 2.5%, XGBoost 3.5%. We applied regularisation (max_depth=4, reg_alpha=0.5, reg_lambda=2.0, min_child_samples=25) and this is what remains.

**Questions:**
- Is a 2.5% train→val gap worth further regularisation effort, or is this negligible given the 10% distribution shift that dominates the test gap?
- Would it be better to report this honestly as "mild overfitting remains" rather than spend more time tuning?

---

## 6. April and May — known mismatch between simulation and reality

April (n=8) and May (n=7) had too few real observations to produce reliable individual estimates — 95% CIs spanning ±0.20. Both were substituted with the **spring season mean (0.43, n=44 across Mar+Apr+May)** in the simulation. This was the statistically defensible choice, but it introduces a known gap: the simulation treats April and May as generic spring days, while the real data suggests April in particular may behave differently (its individual raw estimate was 0.50, vs the spring mean of 0.43).

The real test set runs Dec 2023 – Apr 2026 and includes April and May data. If the model has learned "spring looks like 0.43" from simulation but the real April dinner covers are closer to 0.50, the model will have a systematically wrong prior for those months — contributing to the val→test distribution shift.

**Questions:**
- Is the thin-month substitution (spring mean for Apr/May) the right statistical call, or is there a better approach given such small samples?
- Should we explicitly report April and May as months with higher expected error in the thesis?
- Could per-month error analysis on the test set help isolate how much of the ~10% gap is driven by these two months specifically?

---

## 7. Morning tier scoring — occupancy dominance is an assumption, not a proven relationship

The morning tier scoring rule assigns tiers purely on `hotel_occupancy_rate` thresholds (≤35% → low, ≤65% → medium, >65% → high), with HARD_HIGH overrides for Christmas, New Year's Eve, and New Year's Day. The feature importance from the trained model (occupancy_pct = 69.5%) appears to confirm this — but it is circular: the model was trained on labels that were *generated by* that same occupancy rule, so high importance for occupancy is guaranteed by construction, not discovered from data.

The real question — whether actual morning staffing demand in this restaurant is primarily driven by hotel occupancy, and whether those threshold values (35%, 65%) are correct — has never been statistically tested against observed morning operational data.

**Questions:**
- Is it acceptable to cite feature importance as evidence for a design assumption when the labels were generated from that same assumption?
- Do we have any observed morning data (covers, revenue, staff hours) that could be used to validate whether occupancy genuinely drives morning demand?
- If not, should this be explicitly flagged as an unvalidated assumption in the thesis, separate from the afternoon model which has real covers data as a ground truth?

---

## 8. Greedy vs CP-SAT — thesis framing

Both algorithms are preserved in the codebase to show progression. The thesis narrative is: greedy → identified limitations → CP-SAT as the improvement.

**Questions:**
- Should the ML tier model feed into both greedy and CP-SAT, or only CP-SAT (since greedy is the baseline)?
- How much experimental comparison between the two is expected — qualitative narrative sufficient, or quantitative benchmarks needed?

---

## 9. CP-SAT objective weights — are the ratios defensible?

The scheduler objective function uses five constants. Their absolute values are a scaling choice — CP-SAT only cares about ratios. The ratio structure is what needs defending:

| Weight | Value | Ratio to FILL_WEIGHT | Rationale |
|--------|-------|----------------------|-----------|
| FILL_WEIGHT | 200 | 1.00 | Anchor — unfilled slot is worst outcome |
| STEEP_OVERWORK_PENALTY | 100 | 0.50 | Half as bad as vacancy — work gets done but at welfare/pay cost |
| UNDERWORK_PENALTY | 80 | 0.40 | Financial waste, no service failure |
| CONSTRAINED_FILL_BONUS | 50 | 0.25 | Margin incentive to schedule constrained staff |
| MILD_OVERWORK_PENALTY | 20 | 0.10 | Expected in hospitality, barely discouraged |

FILL_WEIGHT = 200 specifically was chosen so all ratios land on whole numbers with no rounding, and to give filled slots enough weight not to be drowned out by accumulated centihour penalties across a full week.

OVERWORK_THRESHOLD = 1.15: 15% of a 40hr contract = 6 hours ≈ one additional half-day shift, the natural unit of a call-in. Also sits within the EU Working Time Directive's 48hr maximum (1.20× for 40hr contracts).

**Questions:**
- Is the ratio structure (1.00 : 0.50 : 0.40 : 0.25 : 0.10) defensible on operational grounds, or does it require empirical validation?
- Should a sensitivity analysis be run to show how much schedules change if weights vary by ±20%?
- ~~Is the CONSTRAINED_FILL_BONUS framing correct?~~ **Resolved:** `constraint = True` means part-time (30hrs/week). Availability is enforced as a hard constraint in `talent_eligible_for_shift()` before any variable is created. The bonus is a soft preference on top — part-time staff win when both are eligible for the same slot. Financially justified: part-time staff are cheaper per hour across all roles.

---

## 10. Scheduler produces identical schedules every week — ML model is not yet integrated

The CP-SAT solver currently receives staffing levels (`role_count` per shift) from a hardcoded day-of-week lookup. Because that lookup has no occupancy or seasonal signal, the solver produces bit-for-bit identical schedules regardless of what week is being generated.

**Exhibit — two consecutive weeks, Oct 11–17 and Oct 18–24:**

![Week 1: Oct 11–17](figures/scheduler_static_week1_oct11.png)
![Week 2: Oct 18–24](figures/scheduler_static_week2_oct18.png)

The schedules are identical. Monday is always staffed the same way, Sunday always the same — irrespective of hotel occupancy, season, or weather that specific week. This is the "before" state the thesis aims to fix.

**The integration gap — now closed:**

The ML tier model (XGBoost for morning, LightGBM for afternoon) is now wired into the scheduler end to end:
1. `predict_tier(date, occupancy_pct, shift)` in `app/core/schedule/ml/tier_predictor.py` — inference wrapper
2. `apply_staffing_to_periods(tier_override=...)` in the staffing service — tier → `role_count` mapping
3. `occupancy_pct` flows from `POST /generate` body → Redis stream → worker → `SchedulingService` → `ShiftSlotBuilder` → `predict_tier`
4. `temp_mean` defaults to seasonal Budapest averages when not supplied

**"After" — ML-integrated schedule at 72% occupancy (Oct 11–17):**

![72% occupancy — Oct 11–17](figures/scheduler_ml_72pct_oct11.png)

Staffing counts now vary within the week: Friday/Saturday show HIGH-tier counts (Leader 3, Server 4) while mid-week holds at MED. This is the occupancy-aware schedule the thesis integration required.

**Questions:**
- Is demonstrating the before/after difference (static vs occupancy-aware schedules) a sufficient empirical result for the thesis, or does it need quantified evaluation against ground truth?
- What constitutes a meaningful "after" — two weeks with different occupancy producing visibly different staffing patterns?

---

## Notes / answers
*(fill in during meeting)*
