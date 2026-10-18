import joblib
import pandas as pd
from datetime import date
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parents[4] / "models"

# Budapest seasonal temperature defaults (°C) used when temp_mean is not supplied
_SEASONAL_TEMP = {"Spring": 12.0, "Summer": 22.0, "Autumn": 10.0, "Winter": -2.0}


_SPECIAL_DAYS = {
    (1, 1),   # New Year's Day
    (3, 15),  # 1848 Revolution Day
    (5, 1),   # Labour Day
    (8, 20),  # St. Stephen's Day
    (10, 23), # 1956 Revolution Day
    (11, 1),  # All Saints' Day
    (12, 25), # Christmas Day
    (12, 26), # Second day of Christmas
    (12, 31), # New Year's Eve
}

# Label encoder returns "medium"; staffing service expects "med"
normalize_staffing = {
    "medium": "med", 
    "high": "high", 
    "low": "low"}


def _season(month: int) -> str:
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    if month in (9, 10, 11):
        return "Autumn"
    return "Winter"


def _load():
    def _pkl(name):
        return joblib.load(_MODEL_DIR / name)

    return {
        "morning": {
            "model":    _pkl("tier_model_morning.pkl"),
            "features": _pkl("tier_feature_cols_morning.pkl"),
        },
        "afternoon": {
            "model":    _pkl("tier_model_afternoon.pkl"),
            "features": _pkl("tier_feature_cols_afternoon.pkl"),
        },
        "encoder": _pkl("tier_label_encoder.pkl"),
    }


model_artifacts = _load()


def predict_tier(dt: date, occupancy_pct: float, shift: str, temp_mean: float | None = None) -> str:
    """Return "high", "med", or "low" for a given date, occupancy, and shift type.

    shift must be "morning" or "afternoon".
    temp_mean defaults to the seasonal average for Budapest if not supplied.
    """
    season = _season(dt.month)
    if temp_mean is None:
        temp_mean = _SEASONAL_TEMP[season]

    # Superset of all features any shift model might need -- each model selects its own subset
    row = {
        "occupancy_%":    occupancy_pct * 100,
        "occupancy_pct":  occupancy_pct * 100,
        "day_of_week":    dt.weekday(),
        "is_weekend":     int(dt.weekday() >= 5),
        "is_special_day": int((dt.month, dt.day) in _SPECIAL_DAYS),
        "temp_mean":      temp_mean,
        "temp_max":       temp_mean + 3.0,
        "season_Spring":  int(season == "Spring"),
        "season_Summer":  int(season == "Summer"),
        "season_Winter":  int(season == "Winter"),
    }

    arts = model_artifacts[shift]
    model_input = pd.DataFrame([row])[arts["features"]]
    raw = arts["model"].predict(model_input)[0]
    # New models return string labels directly; old models return encoded integers
    if isinstance(raw, str):
        label = raw
    else:
        label = model_artifacts["encoder"].inverse_transform([raw])[0]
    return normalize_staffing[label]
