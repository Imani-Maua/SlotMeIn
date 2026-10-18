# Discussion Points for Supervisor Meeting

## 1. Season-Stratified Test Split

**Question:** Is holding out the last 20% of days per season a defensible evaluation strategy, or does it introduce enough cross-season leakage that the test accuracy is still misleading?

**Context:** A strict chronological cutoff (last 20% of all dates) would place all 56 test days in winter/early spring, making it impossible to evaluate the model on High-demand summer conditions. The season-stratified approach takes the last 20% of days within each season separately, preserving temporal order within seasons while ensuring all demand tiers are represented in the test set.

**What I want to hear:** Whether he considers the cross-season leakage this introduces to be a material threat to validity, and if so, what the preferred alternative would be given that we only have 294 real observations spread unevenly across seasons.


Whether or not I should write the progression that led to generating the 2000 datapoints

55% as defensible

December ramp