# Tier Model Training Log

---

## Run 7 — 2026-10-08 — FINAL ✓
**Ablation:** Drop `day_of_month`, `is_weekend`, `temp_max` from both shifts  
**Train data:** Resort Hotel sim (2015–2017), 685 dates  
**Val data:** Resort sim, season-stratified 15% (121 dates, all 4 seasons)  
**Test data:** Real hotel — Dec 2023 – Apr 2026 (1,676 rows)

### Results

**Morning**
| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 99.7% | 99.2% | 93.5% | +0.5% |
| XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| LightGBM | 99.7% | 98.3% | 98.1% | +1.4% |

**Afternoon**
| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 92.3% | 92.6% | 83.0% | −0.3% |
| XGBoost | 99.4% | 97.5% | 85.2% | +1.9% |
| LightGBM ★ | 100.0% | 98.3% | 87.7% | +1.7% |

### vs Run 6
| Shift | Val Δ | Test Δ | Gap Δ |
|-------|-------|--------|-------|
| Morning | 0.0% | 0.0% | 0.0% |
| Afternoon | +1.6% | 0.0% | −1.6% |

Afternoon overfitting halved (3.3% → 1.7%) at zero cost to test accuracy.

### Final feature sets
- **Morning (6 features):** `occupancy_pct, day_of_week, temp_mean, season_Spring, season_Summer, season_Winter`
- **Afternoon (7 features):** `occupancy_pct, day_of_week, is_special_day, temp_mean, season_Spring, season_Summer, season_Winter`

### Feature importances
**Morning (XGBoost):** occupancy_pct 0.752 · temp_mean 0.130 · season_Winter 0.055 · season_Summer 0.033 · day_of_week 0.018 · season_Spring 0.012  
**Afternoon (LightGBM):** temp_mean 0.289 · day_of_week 0.274 · occupancy_pct 0.274 · is_special_day 0.085 · season_Spring 0.051 · season_Winter 0.023 · season_Summer 0.003

### Overfitting assessment
- **Morning:** No meaningful overfitting. Gap +0.7%, test (99.3%) matches val (99.2%) almost exactly.
- **Afternoon:** Minimal overfitting at 1.7%. Remaining ~11% val→test gap is structural distribution shift — confirmed across all 7 runs. The ~88% test ceiling is the honest ceiling given simulation-to-real transfer.

### Saved artefacts
- `models/tier_model_morning.pkl` — XGBoost
- `models/tier_model_afternoon.pkl` — LightGBM
- `models/tier_feature_cols_morning.pkl` — 6 features
- `models/tier_feature_cols_afternoon.pkl` — 7 features
- `models/tier_label_encoder.pkl` — LabelEncoder fitted on [high, low, medium]
- `thesis/figures/model_confusion_matrices.png`

---

## Run 6 — 2026-10-08 (Ablation — drop `is_special_day` from morning)
**Change from Run 5:** `is_special_day` removed from morning feature set. Afternoon unchanged.  
**Motivation:** Morning `is_special_day` importance was 0.000 in Run 5 — feature contributed nothing.

### Results — Morning (without `is_special_day`)
| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 99.7% | 99.2% | 95.7% | +0.5% |
| XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| LightGBM | 99.7% | 98.3% | 98.1% | +1.4% |

### vs Run 5 (with `is_special_day`)
| Model | Test Δ |
|-------|--------|
| Random Forest | +0.7% (95.0% → 95.7%) |
| XGBoost | 0.0% (99.3% → 99.3%) |
| LightGBM | 0.0% (98.1% → 98.1%) |

### Assessment
Dropping `is_special_day` from morning makes no difference to XGBoost and LightGBM, and slightly improves RF test accuracy. Confirmed the feature is noise for morning. Morning and afternoon now use separate feature sets.

### Final feature sets
- **Morning (9 features):** `occupancy_pct, day_of_week, day_of_month, is_weekend, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`
- **Afternoon (10 features):** `occupancy_pct, day_of_week, day_of_month, is_weekend, is_special_day, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`

**Saved as:** `tier_feature_cols_morning.pkl`, `tier_feature_cols_afternoon.pkl`

**Note:** Any inference code previously loading `tier_feature_cols.pkl` must be updated to load the shift-specific file.

---

## Run 5 — 2026-10-08
**Approach:** Resort sim + season-stratified val + `day_of_month` added as feature  
**Change from Run 3:** Added `day_of_month` (1–31) to feature set so the model can learn within-month patterns  
**Train data:** Resort Hotel sim (2015–2017), 685 dates  
**Val data:** Resort sim, season-stratified 15% (121 dates, all 4 seasons)  
**Test data:** Real hotel — Dec 2023 – Apr 2026 (1,676 rows)

### Results

**Morning**
| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 99.7% | 99.2% | 95.0% | +0.5% |
| XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| LightGBM | 99.9% | 98.3% | 98.1% | +1.5% |

**Afternoon**
| Model | Train | Val | Test | Gap |
|-------|-------|-----|------|-----|
| Random Forest | 92.0% | 92.6% | 82.6% | −0.6% |
| XGBoost | 99.6% | 95.9% | 85.0% | +3.7% |
| LightGBM ★ | 100.0% | 96.7% | 87.7% | +3.3% |

### Feature importances (LightGBM afternoon)
| Feature | Importance |
|---------|-----------|
| day_of_week | 0.263 |
| temp_mean | 0.229 |
| occupancy_pct | 0.224 |
| day_of_month | 0.100 |
| is_special_day | 0.069 |
| temp_max | 0.056 |
| season_Spring | 0.047 |
| season_Winter | 0.008 |
| is_weekend | 0.002 |
| season_Summer | 0.001 |

### Assessment
`day_of_month` is genuinely learned (4th most important afternoon feature, 10%). However it did not improve test accuracy (87.7% unchanged vs Run 3). The within-month pattern the model extracted from the simulation does not align with the real restaurant's within-month pattern — adding noise at generalisation time. The afternoon test ceiling (~87–88%) holds across all approaches, confirming the gap is structural distribution shift.

**Features:** `occupancy_pct, day_of_week, day_of_month, is_weekend, is_special_day, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`

---

## Run 4 — 2026-10-07
**Approach:** Resort sim + season-stratified val + within-month cover rate ramps computed per month  
**Outcome:** Identical to Run 3 — ramps computed `dinner_cover_rate_base` but this column was not used in tier labels or model features. No effect on training data.

---

## Run 3 — 2026-10-07
**Approach:** Resort Hotel simulation only, season-stratified val split  
**Train data:** Resort Hotel sim (2015–2017), 806 dates, 685 in train  
**Val data:** Resort Hotel sim, 15% sampled from each season (121 dates, all 4 seasons represented)  
**Test data:** Real hotel data — Dec 2023 – Apr 2026 (1,676 rows)

### Val season breakdown
| Season | Train dates | Val dates |
|--------|------------|-----------|
| Spring | 156 | 28 |
| Summer | 209 | 37 |
| Autumn | 166 | 29 |
| Winter | 154 | 27 |
| **Total** | **685** | **121** |

### Results

**Morning**
| Model | Train | Val | Test | Train→Val gap |
|-------|-------|-----|------|---------------|
| Random Forest | 99.7% | 99.2% | 96.2% | +0.5% |
| XGBoost ★ | 99.9% | 99.2% | 99.3% | +0.7% |
| LightGBM | 99.9% | 98.3% | 98.1% | +1.5% |

**Afternoon**
| Model | Train | Val | Test | Train→Val gap |
|-------|-------|-----|------|---------------|
| Random Forest | 92.0% | 92.6% | 82.9% | −0.6% |
| XGBoost | 99.4% | 95.9% | 84.8% | +3.5% |
| LightGBM ★ | 100.0% | 97.5% | 87.7% | +2.5% |

★ = selected (best val accuracy)

### Overfitting assessment
- **Morning — No overfitting.** Train→val gaps are 0.5–1.5%. Test tracks val closely (XGBoost test 99.3% ≈ val 99.2%). The model generalises well to real data.
- **Afternoon — Mild overfitting, dominant distribution shift.** LightGBM train→val gap is 2.5%, XGBoost 3.5% — these are real but small. The bigger story is the val→test gap of ~10% across all models (e.g. LightGBM val 97.5% → test 87.7%). This is **distribution shift**: the simulation's afternoon feature distribution differs from the real restaurant's. No regularisation configuration has closed this gap — a 24-config sweep (Run 2) confirmed it is structural.

### Hyperparameters
- **Random Forest:** n_estimators=300, max_depth=6, min_samples_leaf=10, max_features=sqrt
- **XGBoost:** n_estimators=500, max_depth=4, lr=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=2.0, min_child_weight=5, early_stopping=30
- **LightGBM:** n_estimators=500, max_depth=4, lr=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.5, reg_lambda=2.0, min_child_samples=25, num_leaves=20, early_stopping=30

### Features
`occupancy_pct, day_of_week, is_weekend, is_special_day, temp_mean, temp_max, season_Spring, season_Summer, season_Winter`

---

## Run 2 — 2026-10-07
**Approach:** Resort Hotel sim (train) + City Hotel sim (val), 24-config regularisation sweep  
**Key finding:** No configuration reduced afternoon train→val gap below ~1%. Confirmed gap is distribution shift (resort sim ≠ city sim feature distributions), not overfitting.  
**Best afternoon:** LightGBM — Train 100%, Val 98.7%, Test 89.9%, gap 1.3%

---

## Run 1 — 2026-10-07
**Approach:** Resort Hotel sim only, temporal 70/15/15 split  
**Problem:** Val and test windows fell entirely in May–Sep 2017 (summer). Afternoon tier is deterministically HIGH in summer → 100% test accuracy. Not a real result.  
**Fix:** Switched to cross-dataset evaluation (sim → real hotel test set) and fixed val split in Run 3.
