from datetime import datetime, time, timedelta
from app.core.schedule.allocator.entities import weekRange
from app.core.schedule.schema import inputDate
from pathlib import Path
import json

def map_label_to_time(label: str):
    label = label.lower()
    lookup = {
        'am': (time(6,0), time(15,0)),
        'pm': (time(15,0), time(23,30)),
        'lounge': (time(11,0), time(23,59))
    }
    return lookup.get(label, (time(6,0), time(15,0)))

def create_datetime(date, time):
    return datetime.combine(date, time)

def fetch_all_shifts():
    base_path = Path(__file__).parent.parent.parent
    json_path = base_path/"config"/"shifts.json"
    with open(json_path) as p:
        shifts = json.load(p)['shifts']
    return shifts

def fetch_staffing_req():
    base_path = Path(__file__).parent.parent.parent.parent
    json_path = base_path/"config"/"staffing.json"
    with open(json_path) as p:
        staffing = json.load(p)['staffing']
        return staffing

def get_week_range(start_date: inputDate):
    date_object = datetime.strptime(str(start_date.start_date), "%Y-%m-%d")
    end = date_object + timedelta(days=6)
    week_range = weekRange(start_date=date_object, end_date=end)
    return week_range


