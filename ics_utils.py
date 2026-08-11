import csv
import requests
from datetime import datetime
import pytz

def load_sheet(csv_url):
    r = requests.get(csv_url)
    r.raise_for_status()
    rows = list(csv.DictReader(r.text.splitlines()))
    return rows

def to_dt(date_str, time_str, tz):
    """Convert sheet date+time into ICS datetime format."""
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt = tz.localize(dt)
    return dt.strftime("%Y%m%dT%H%M%S")

def escape_description(text):
    """ICS requires escaped newlines."""
    if not text:
        return ""
    return text.replace("\n", "\\n")
