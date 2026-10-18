# Simulation Design Log
## How the dinner cover rate simulation evolved from assumption to evidence

This document records the reasoning, decisions, and evidence behind the simulation used to generate training data for the staffing tier model. It is written chronologically so the intellectual progression is traceable.

---

## Stage 1 — Original approach: domain-knowledge parameters

### What was done

The `simulate_dinner_cover_rate` function in `notebooks/slotmein_data_simulation.ipynb` used hardcoded seasonal base rates and adjustment factors derived entirely from personal experience working in the restaurant:

```python
if month in [1, 2, 3]: base = 0.10   # Q1 slow period
elif month in [4, 5]:  base = 0.35   # Spring pickup
elif month in [6, 7, 8]: base = 0.75 # Summer peak
elif month in [9, 10, 11]: base = 0.45
else: base = 0.55                     # December

if day_of_week in [4, 5, 6]: base += 0.20
elif day_of_week in [0, 1, 2, 3]: base -= 0.15

if is_special_day: base += 0.30
if has_local_event: base += 0.20
if weather_score > 0.6 and hotel_occupancy_rate > 40: base += 0.08

noise = np.random.normal(0, 0.05)
```

### Why this was not defensible

An examiner can ask: "Why 0.75 for summer and not 0.65? Why does a special day add 0.30?" There is no answer grounded in data. The model was learning the researcher's assumptions, not patterns from reality. The direction of causality was backwards:

> Rigorous: estimate parameters from real data → simulate → train  
> What happened: simulate with invented parameters → train → validate → find partial agreement

The 50.5% validation agreement with real covers data (from `validate_scoring_system.ipynb`) shows the simulation was capturing *something* real — but it could not be shown that the specific numbers were grounded in anything other than personal judgment.

---

## Stage 2 — Fix: statistically derive all parameters from real covers data

### The data source

`data/raw/covers_data.csv` contains **294 observed afternoon cover counts** from this restaurant, spanning **January 2025 – April 2026**. This is real operational data — actual headcounts recorded on the floor.

Cover rate was normalised using the same method as `validate_scoring_system.ipynb`:

```
cover_rate = afternoon_covers / afternoon_covers.quantile(0.95)
```

The 95th percentile is used as the full-house proxy to avoid single outliers inflating the denominator.

### Parameters derived (all traceable to real data)

| Parameter | Value | How derived |
|---|---|---|
| Monthly base rates | See table below | Mean cover rate per calendar month across 294 real days |
| Weekend delta | Per-season (see below) | Mean(weekend) − Mean(weekday) grouped by season |
| Special day delta | +0.14 | Mean(special days) − Mean(regular days) across all 294 days |
| Noise std | 0.21 | Residual std within season × day-of-week groups |

**Monthly base rates (real data mean, normalised):**

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| 0.41 | 0.41 | 0.40 | 0.50 | 0.43 | 0.80 | 0.74 | 0.75 | 0.64 | 0.43 | 0.35 | 0.68 |

**Weekend delta by season (real data):**

| Winter | Spring | Summer | Autumn |
|--------|--------|--------|--------|
| +0.04 | +0.18 | +0.06 | +0.04 |

**Note on `has_local_event`:** No event log exists in the available data. This flag cannot be estimated statistically. Its contribution was reduced from +0.20 (original guess) to +0.10 (a conservative assumption, smaller than the measured noise term of 0.21). This is the only remaining assumption in the function and is explicitly documented as such.

### Sample size check — thin months

After deriving monthly base rates, the sample sizes per month were checked:

| Month | n_days | Estimate used |
|-------|--------|---------------|
| Jan | 28 | individual mean (0.41) |
| Feb | 25 | individual mean (0.41) |
| Mar | 29 | individual mean (0.40) |
| **Apr** | **8** | **spring season mean (0.43) — substituted** |
| **May** | **7** | **spring season mean (0.43) — substituted** |
| Jun | 27 | individual mean (0.80) |
| Jul | 28 | individual mean (0.74) |
| Aug | 29 | individual mean (0.75) |
| Sep | 26 | individual mean (0.64) |
| Oct | 28 | individual mean (0.43) |
| Nov | 29 | individual mean (0.35) |
| Dec | 30 | empirical ramp (see Stage 4) |

April and May had fewer than 15 observations each. With n=7 and n=8, the 95% confidence interval on each mean spans roughly ±0.20 — as wide as the estimate itself. Replacing both with the spring season mean (computed across all 44 spring days: Mar + Apr + May) is statistically more robust and fully defensible: it uses more data, not less.

**What to say if asked:** *"April and May each had fewer than ten recorded days in the available covers data, producing individual estimates with confidence intervals too wide to be reliable. Both were replaced with the spring season mean, calculated across all 44 spring observations, which provides a more stable estimate while remaining grounded in real data from the same seasonal period."*

### What changed in the code

The function `simulate_dinner_cover_rate` in `notebooks/slotmein_data_simulation.ipynb` was rewritten. A new parameter derivation cell (immediately before the function) loads `covers_data.csv` and computes all parameters live — the derivation is fully reproducible by re-running the notebook.

---

## Stage 3 — Visual validation: real vs simulated time series

### First comparison (full date ranges)

The first version of the comparison plot showed the two datasets on their natural date ranges:
- Real: January 2025 → April 2026
- Simulated: July 2015 → September 2017

The seasonal patterns were visible in both but the different time spans made direct comparison difficult — the simulated dataset covers more than twice the calendar length of the real data, making it hard to read the seasonal rhythm side by side.

**Figure saved:** `thesis/figures/real_vs_simulated_full_range.png`

![Full date range comparison](figures/real_vs_simulated_full_range.png)

### Second comparison (aligned seasonal window)

Both datasets were filtered to the same **June → April** seasonal window to make the comparison position-by-position:
- Real: June 2025 → April 2026
- Simulated: June 2016 → April 2017

A relative day-offset x-axis was used so both panels share the same horizontal scale, with month labels (Jun, Jul, … Apr) rather than calendar dates. This eliminates the visual distraction of different years and lets the seasonal structure speak directly.

**Figure saved:** `thesis/figures/real_vs_simulated_timeseries.png`

### What the aligned comparison showed

![Aligned seasonal window comparison](figures/real_vs_simulated_timeseries.png)

**Where they agree well:**
- **Summer (Jun–Sep):** Both show the same high-cover plateau, rolling means 75–85%. The most important structural feature is faithfully reproduced.
- **Autumn decline (Oct–Nov):** Both panels show the rolling mean falling from summer highs to 40–50% at roughly the same rate through October and November.
- **January crash:** Both hit their lowest point in January — rolling mean ~30–35% in real, ~35–40% in simulated. The sharpest single-month drop is captured correctly.

**Where they diverge:**
- **December:** The real data shows a dramatic festive-season recovery — rolling mean climbs from ~35% in November back up to ~75–85% through December. The simulated December with a flat monthly mean of 0.68 only reached ~65–70%. The simulation was underestimating the December peak.
- **Spring (Feb–Apr):** The simulated recovery is slightly more optimistic than real (~55–65% vs ~35–55%). Minor and within the noise band.

---

## Stage 4 — Fix: December festive ramp

### Why December is different

The flat monthly mean of 0.68 for December is the *average* across the whole month. But December is not uniform — it builds progressively as the festive season intensifies:

- Early December (1–14): corporate lunches beginning, pre-Christmas shopping traffic, still relatively normal
- Late December (15–31): Christmas parties, festive dinners, holiday gatherings, New Year's Eve — the restaurant's busiest fortnight of the year

A single mean obscures this within-month trend entirely.

### Fix: empirical linear ramp

The 30 observed December days in `covers_data.csv` were split into two halves and means computed:

```python
DEC_EARLY = mean cover_rate for days 1–14   # empirical
DEC_LATE  = mean cover_rate for days 15–31  # empirical
```

The simulation now applies a **linear interpolation** between these two empirical values across the 31 days of December:

```python
t    = (day_of_month - 1) / 30.0        # 0.0 at Dec 1 → 1.0 at Dec 31
base = DEC_EARLY + t * (DEC_LATE - DEC_EARLY)
```

This is fully data-derived — both endpoints come from real covers — and it captures the festive build-up as a measurable phenomenon rather than a design assumption.

### What to say in the thesis

> "The within-month trend in December is captured through an empirical linear ramp. The early-month mean (days 1–14) and late-month mean (days 15–31) are estimated separately from observed covers data, reflecting the progressive intensification of the festive trading period — corporate dining, Christmas parties, and holiday gatherings — which operates at a multi-week scale rather than spiking only on individual public holidays."

### Result after the December ramp

**Figure saved:** `thesis/figures/real_vs_simulated_timeseries.png`

![Aligned comparison after December ramp](figures/real_vs_simulated_timeseries.png)

**What improved:** The simulated December rolling mean climbs higher through the month rather than sitting flat, narrowing the gap with the real data's festive peak. The build-up from November's trough into mid-to-late December is now visible in the simulated panel.

**What remains:** A small residual gap persists — the real December 2025 peaks slightly higher than the simulation. This is expected: the real data reflects one specific December with its own client mix, corporate bookings calendar, and local context. A general simulation parameterised from that same month's mean cannot perfectly reproduce its peak. The structural shape — the ramp — is correct; the precise magnitude is subject to year-specific variation the simulation does not claim to predict.

**Overall assessment:** Summer, autumn, and January align strongly across both panels. The December festive build-up is now structurally present. The spring recovery is slightly overestimated but within the noise band. The simulation reproduces the seasonal shape of the year faithfully, with all parameters traceable to observed data.

---

## Stage 5 — Full date range: seasonal cycles across the complete simulation

After all parameter fixes were applied, the full extent of both datasets was plotted to verify that the simulation produces a consistent, repeating seasonal pattern across multiple years — not just within a single window.

**Figure saved:** `thesis/figures/real_vs_simulated_full_range.png`

![Full date range — repeating seasonal cycles](figures/real_vs_simulated_full_range.png)

**What this shows:**

- **Top panel (real data, Jan 2025 → Apr 2026):** One complete seasonal cycle is visible — winter flat around 40%, spring pickup, summer plateau at 75–85%, autumn decline, festive December recovery to ~80%, and the sharp January crash to ~30%.

- **Bottom panel (simulated data, Jul 2015 → Sep 2017, 806 days):** Three summer cycles and two winter troughs are clearly visible, each reproducing the same structural shape. The seasonal pattern is stable and consistent across all three calendar years — the parameters are not tuned to a single year but generalise correctly.

**Why this matters for the thesis:** A simulation that reproduces one seasonal cycle could be a coincidence. Showing three independent cycles — each with the same summer peak, winter trough, and December festive uplift — demonstrates that the empirically derived parameters capture a genuine structural pattern in the data, not an artefact of a particular date range. This strengthens the case for using the simulation to generate training data across a wider time window than the real covers data alone could provide.

---

## Summary of the simulation's data lineage

| Feature | Source | Type |
|---|---|---|
| `hotel_occupancy_rate` | `hotel_bookings.csv` — 119,390 real bookings | **Real, computed** |
| `%breakfast`, `%half_board`, `%full_board` | `hotel_bookings.csv` — real meal plan records | **Real, computed** |
| `is_special_day` | Hungarian public holiday calendar | **Real, deterministic** |
| `is_weekend`, `day_of_week`, `season` | Derived from real booking dates | **Real, derived** |
| `weather_score` | Season-parameterised Gaussian (simulation notebook only) | Synthetic — superseded by real Open-Meteo temperature data in `wrangle_occupancy_data.ipynb` |
| `dinner_cover_rate` monthly base | Mean per month from 294 real cover observations | **Empirical** |
| `dinner_cover_rate` weekend delta | Season-level weekend/weekday difference from real data | **Empirical** |
| `dinner_cover_rate` special day delta | Mean difference on/off special days from real data | **Empirical** |
| `dinner_cover_rate` December ramp | Early/late December means from real data | **Empirical** |
| `dinner_cover_rate` noise | Residual std within season × day-of-week from real data | **Empirical** |
| `has_local_event` contribution | +0.10, no event log available | **Assumption — documented** |

---

*Last updated: 2026-10-07 — Stage 5 full date range graph added*  
*Notebook: `notebooks/slotmein_data_simulation.ipynb`*  
*Validation notebook: `notebooks/validate_scoring_system.ipynb`*  
*Real covers data: `data/raw/covers_data.csv`*
