# CP-SAT Objective Weights — Design Rationale

The scheduler maximises a single objective function:

```python
model.maximize(
    FILL_WEIGHT * sum(fill_terms)
    + CONSTRAINED_FILL_BONUS * sum(constrained_bonus_terms)
    - sum(penalty_terms)
)
```

---

## Wage data

All weight ratios are grounded in actual wage records from the restaurant. The service charge is a monthly pool distribution tied to total hotel revenue — it does not vary with individual hours worked and is therefore irrelevant to per-hour scheduling cost calculations. Only base salary determines the marginal cost of each scheduling decision.

**Consensus hotel monthly revenue: ~21.9M HUF**
Derived independently from each role's service charge percentage and known SC range — consistent across all four roles, confirming the wage figures are internally valid.

### Full wage table

| Role | Contract | Base/month | SC/month | Total/month | Base/hr | Total/hr |
|------|----------|-----------|---------|------------|--------|---------|
| Manager | Full-time | 1,000,000 | 1,000,000 (flat) | 2,000,000 | 5,780 | 11,561 |
| Leader | Full-time | 492,000 | 328,500 (1.5%) | 820,500 | 2,844 | 4,743 |
| Bartender | Full-time | 392,000 | 87,600 (0.4%) | 479,600 | 2,266 | 2,772 |
| Bartender | Part-time | 294,566 | 43,800 (0.2%) | 338,366 | 2,266 | 2,603 |
| Server | Full-time | 392,000 | 219,000 (1.0%) | 611,000 | 2,266 | 3,532 |
| Server | Part-time | 294,566 | 153,300 (0.7%) | 447,866 | 2,266 | 3,445 |
| Runner | Full-time | 292,000 | 109,500 (0.5%) | 401,500 | 1,688 | 2,321 |
| Runner | Part-time | 219,422 | 65,700 (0.3%) | 285,122 | 1,688 | 2,193 |
| Hostess | Full-time | 250,000 | 65,700 (0.3%) | 315,700 | 1,445 | 1,825 |
| Hostess | Part-time | 187,861 | 21,900 (0.1%) | 209,761 | 1,445 | 1,614 |

Part-time = 30 hours/week (75% of full-time). Base salary pro-rated accordingly. Part-time staff are cheaper per hour across every role due to pro-rated base and reduced service charge entitlement.

---

## Underwork vs overwork — what costs more?

This is the foundational question for the penalty weights. The answer has two layers.

### In absolute wage terms: overtime is the larger bill

For a Server working 2 hours beyond contract (Hungarian overtime rate: 150% of base):

| Scenario | Employer pays | Work received |
|----------|--------------|---------------|
| Underwork (2hrs short) | 2 × 2,266 = **4,532 HUF** | Nothing |
| Overtime (2hrs over) | 2 × 2,266 × 1.5 = **6,798 HUF** | 2 hours of work |

Overtime is the larger payroll item.

### In terms of pure waste: underwork costs more

The objective function separates the **value of work** (FILL_WEIGHT) from the **cost of scheduling inefficiency** (penalty terms). Penalty terms only measure extra cost above what was already budgeted:

| Scenario | Extra cost above budget | Value received |
|----------|------------------------|----------------|
| Underwork | 2,266 HUF/hr — paying for nothing | Zero |
| Overtime premium | 1,133 HUF/hr (the 50% above base) | 2hrs work + revenue |

**Underwork costs exactly 2× the overtime premium per hour — consistently across every role, because the 2:1 ratio holds regardless of base salary level.**

This is the financially derived ratio: **UNDERWORK : STEEP_OVERWORK premium = 2 : 1**

---

## The welfare premium — why our weights invert the financial ratio

The financial data says underwork should be penalised 2× more than steep overwork. Our weights do the opposite:

```
Financial reality:   UNDERWORK : STEEP_OVERWORK = 2.0 : 1.0
Implemented weights: UNDERWORK : STEEP_OVERWORK = 0.8 : 1.0  (80 vs 100)
Implied welfare premium on overwork: 2.5×
```

This inversion is a deliberate design choice. Overwork carries costs that do not appear in payroll data:

- **Burnout and fatigue** — degraded service quality during the shift and increased sick days afterwards
- **Staff turnover** — chronically overworked employees leave; replacement and retraining costs are significant in hospitality
- **EU Working Time Directive compliance** — legal exposure if overwork becomes systematic

The model treats overwork as **2.5× more harmful** than pure financial cost-minimisation would require. This is the quantified value the scheduler places on staff welfare and retention above the hourly wage cost.

*"Wage records confirm a financial underwork-to-overtime-premium ratio of 2:1, consistent across all roles. The implemented weights invert this ratio by a factor of 2.5, representing an explicit welfare premium: the scheduler treats steep overwork as 2.5× more costly than financial optimisation alone would require, capturing the long-term costs of burnout and turnover that are absent from payroll data."*

---

## The ratios

| Weight | Value | Ratio to FILL_WEIGHT | Financial basis |
|--------|-------|----------------------|-----------------|
| `FILL_WEIGHT` | 200 | 1.00 | Anchor — revenue at risk from unfilled slot (~18× underwork cost per shift) |
| `STEEP_OVERWORK_PENALTY` | 100 | 0.50 | Financially 0.25; raised to 0.50 by 2.5× welfare premium |
| `UNDERWORK_PENALTY` | 80 | 0.40 | Financially 0.50; reduced to 0.40 by welfare premium |
| `CONSTRAINED_FILL_BONUS` | 50 | 0.25 | Cost-efficiency incentive for part-time staff |
| `MILD_OVERWORK_PENALTY` | 20 | 0.10 | Operational noise — barely discouraged |

### FILL_WEIGHT = 200 — the anchor

Revenue analysis using dinner service data confirms FILL_WEIGHT must dominate all other terms. At a medium dinner service (48 covers, 50,000 HUF average spend):

- Revenue attributable per server: ~800,000 HUF per service
- Revenue at risk from one unfilled server slot (15–25% of section lost): **120,000–200,000 HUF**
- Server underwork cost for same 4-hour shift: **9,064 HUF**
- Revenue risk is approximately **18× the underwork cost** for the same shift

This confirms FILL_WEIGHT must be the largest weight. The absolute value of 200 is a scaling anchor — CP-SAT produces identical schedules at 20 or 20,000, as only ratios matter. 200 was chosen so all other weights land on whole numbers with clean ratios.

### STEEP_OVERWORK_PENALTY = 100 (ratio 0.50)

Financially, the overtime premium is 0.5× base hourly — the pure financial penalty ratio would be 0.25 (half of underwork's 0.50). The implemented ratio of 0.50 is 2× the financial value, reflecting the 2.5× welfare premium. Working past 115% of contracted hours is treated as a welfare failure, not just a cost item.

### UNDERWORK_PENALTY = 80 (ratio 0.40)

Financially, underwork costs 1.0× base hourly — pure waste, nothing produced. The pure financial ratio relative to FILL_WEIGHT would be 0.50. The implemented ratio of 0.40 is slightly below this, reflecting that underwork (financial waste) is less harmful than steep overwork (financial cost plus welfare risk). The solver accepts some underwork to fill slots.

### CONSTRAINED_FILL_BONUS = 50 (ratio 0.25)

`constraint = True` means **part-time employee** (30 hours/week, 75% of full-time).

**How it works — two enforced layers:**

1. **Hard constraint (availability window):** `talent_eligible_for_shift()` checks the `window` field on `talentAvailability` before creating any decision variable. A part-time employee cannot be assigned to a shift outside their declared availability — this is enforced before the solver runs.

2. **Soft preference (the bonus):** When both a constrained (part-time) and unconstrained (full-time) talent are eligible for the same slot, the solver sees:
   - Assign full-time → reward 200
   - Assign part-time → reward 250

   It picks the part-time person. This is the intent: when there is a choice, the constrained person gets the slot because they have fewer opportunities.

**Why the bonus is necessary:**

Without it, the solver has two reasons to skip part-time staff:
1. Fewer available hours → fewer slots they can even be assigned to
2. Smaller contracted hours (30 vs 40) → less underwork penalty pressure to motivate the solver to find them shifts

**Why the bonus is financially justified:**

Part-time staff are cheaper per hour across every role (pro-rated base, lower SC). Scheduling them when available is cost-efficient for the restaurant. The bonus aligns the solver's incentive with the restaurant's financial preference — the cheaper option wins when both are eligible.

*"Part-time staff work 30 hours per week and are cheaper per hour across all roles. Their narrower availability means the solver, without intervention, fills shifts with always-available full-time staff. The 25% bonus corrects this bias, aligning the solver's incentive with the restaurant's preference for the more cost-efficient option when both a constrained and unconstrained talent are eligible for the same slot."*

### MILD_OVERWORK_PENALTY = 20 (ratio 0.10)

Working between 100–115% of contracted hours is operational noise in a restaurant — tables stay late, colleagues call in sick, service runs over. The solver is nudged away from it but not blocked. The 1:5 ratio between mild and steep overwork (20:100) reflects that these are categorically different: the mild band is routine, the steep band is a welfare concern.

---

## OVERWORK_THRESHOLD = 1.15

The boundary between mild and steep overwork. For a 40-hour contract:

- 1.15 × 40 = **46 hours** — approximately one additional half-day shift per week
- The natural operational unit of a single call-in: covering one absent colleague
- Sits within the **EU Working Time Directive** 48-hour maximum (1.20× for 40hr contracts) — a safety margin below the legal ceiling
- Below 1.15: overtime is explicable by a single incident. Above 1.15: something systematic is wrong.

---

## Priority ordering

```
Fill slot > Avoid steep overwork > Avoid underwork > Schedule part-time > Avoid mild overwork
   1.00           0.50                  0.40                0.25                0.10
```

The solver always prefers to fill a slot. It strongly resists steep overwork (welfare premium embedded). It accepts mild overwork and minor underwork as the cost of full coverage. It actively prefers part-time staff over full-time when both are eligible.

---

## What still needs defending

- **Sensitivity analysis:** varying each weight by ±20% and showing output schedules are stable would make the choices empirically robust, not just logically grounded.
- **Revenue loss estimate (15–25%):** the assumption that one unfilled server slot risks 15–25% of section revenue is domain-informed but not measured. A more precise figure would strengthen the FILL_WEIGHT justification.
