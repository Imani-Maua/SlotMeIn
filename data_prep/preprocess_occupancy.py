"""
preprocess_occupancy.py
-----------------------
Reads hotel_occupancy.csv, selects the features relevant to
staffing prediction, engineers derived date/season columns,
drops pre-opening zero rows, and saves a clean parquet + csv.

Output:
    data_prep/outputs/occupancy_features.csv
    data_prep/outputs/occupancy_features.parquet
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "hotel_occupancy.csv"
OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(RAW_CSV)
print(f"Loaded {len(df):,} rows")


df["Date"] = pd.to_datetime(
    df["Date"].str.split(" ").str[0],   # drop the day-name part e.g. 'Mon'
    format="%d-%m-%y"
)


pre_open_mask = df["Total_Occ"] == 0
n_dropped = pre_open_mask.sum()
df = df[~pre_open_mask].reset_index(drop=True)
print(f"Dropped {n_dropped:,} pre-opening zero rows → {len(df):,} usable rows")



KEEP = [
    "Date",
    "Total_Occ",       # total rooms occupied (absolute count)
    "Occ_Pct",         # occupancy percentage → strongest demand signal
    "Arr_Rooms",       # arrivals → drives morning/breakfast peaks
    "Dep_Rooms",       # departures → drives morning pressure
    "Deduct_Group",    # group bookings → predictable bulk demand
    "Deduct_Indiv",    # individual bookings → variable demand
    "Adl_Chl",         # total guests (adults + children) → better than rooms
]

df = df[KEEP].copy()

df["day_of_week"]   = df["Date"].dt.dayofweek          # 0=Mon … 6=Sun
df["day_name"]      = df["Date"].dt.day_name()          # readable label
df["month"]         = df["Date"].dt.month
df["month_name"]    = df["Date"].dt.month_name()
df["year"]          = df["Date"].dt.year
df["is_weekend"]    = df["day_of_week"].isin([5, 6]).astype(int)

def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4, 5):
        return "Spring"
    elif month in (6, 7, 8):
        return "Summer"
    else:
        return "Autumn"

df["season"] = df["month"].apply(get_season)

# Proportion of guests in groups vs individual
df["group_ratio"] = df["Deduct_Group"] / df["Total_Occ"].replace(0, 1)

# Net guest flux: more arrivals than departures = busier day incoming
df["arrival_pressure"] = df["Arr_Rooms"] - df["Dep_Rooms"]

# Avg guests per occupied room (density signal)
df["guests_per_room"] = df["Adl_Chl"] / df["Total_Occ"].replace(0, 1)


print("\nFeature summary:")
print(df.dtypes)
print(f"\nDate range: {df['Date'].min().date()} → {df['Date'].max().date()}")
print(f"Total rows : {len(df):,}")
print(f"\nOcc_Pct stats:\n{df['Occ_Pct'].describe().round(2)}")
print(f"\nSeason distribution:\n{df['season'].value_counts()}")
print(f"\nWeekend vs Weekday:\n{df['is_weekend'].value_counts().rename({0:'Weekday', 1:'Weekend'})}")

out_csv = OUT_DIR / "occupancy_features.csv"

df.to_csv(out_csv, index=False)

print(f"\n✅ Saved:\n  {out_csv}")
