import json
import urllib.request
from datetime import date

from app.config.config import Settings

_settings = Settings()
_URL = (
    f"{_settings.WEATHER_API_URL}"
    f"?latitude={_settings.WEATHER_LAT}&longitude={_settings.WEATHER_LON}"
    "&daily=temperature_2m_mean"
    "&forecast_days=14"
    "&timezone=Europe%2FBudapest"
)

_SEASONAL_FALLBACK = {"Spring": 12.0, "Summer": 22.0, "Autumn": 10.0, "Winter": -2.0}


def _season(month: int) -> str:
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    if month in (9, 10, 11):
        return "Autumn"
    return "Winter"


def fetch_forecast(start_date: date, days: int = 8) -> dict[str, float]:
    """Return {date_str: temp_mean_celsius} for `days` days starting at start_date.

    Falls back to seasonal averages if the API is unreachable.
    """
    try:
        with urllib.request.urlopen(_URL, timeout=5) as resp:
            data = json.loads(resp.read())
        dates = data["daily"]["time"]
        temps = data["daily"]["temperature_2m_mean"]
        forecast = {dt: temp for dt, temp in zip(dates, temps) if temp is not None}
        return forecast
    except Exception:
        # Network unavailable or API changed — degrade gracefully
        from datetime import timedelta
        return {
            str(start_date + timedelta(days=i)): _SEASONAL_FALLBACK[_season((start_date + timedelta(days=i)).month)]
            for i in range(days)
        }
