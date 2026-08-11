import csv
import requests
import yaml
from datetime import datetime
import pytz

def load_sheet(csv_url):
    r = requests.get(csv_url)
    r.raise_for_status()
    rows = list(csv.DictReader(r.text.splitlines()))
    return rows

def to_dt(date_str, time_str, tz):
    date_str = date_str.strip()
    time_str = time_str.strip()
    
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt = tz.localize(dt)
    return dt.strftime("%Y%m%dT%H%M%S")

def escape_description(text):
    """ICS requires escaped newlines."""
    if not text:
        return ""
    return text.replace("\n", "\\n")

def generate_ics(rows, tz, audience):
    events = []

    desc_column = "Description (Parents)" if audience == "parents" else "Description (Animateurs)"

    for row in rows:
        start_date = row["Start_Date"].strip()
        start_time = row["Start_Time"].strip()
        end_date = row["End_Date"].strip() if row["End_Date"].strip() else start_date
        end_time = row["End_Time"].strip()
        
        start = to_dt(start_date, start_time, tz)
        end = to_dt(end_date, end_time, tz)

        desc = escape_description(row[desc_column])

        uid = f"{audience}-{start_date}-{row['Title'].replace(' ', '-')}"
        title = row["Title"]
        location = row["Location"]

        event = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{start}
DTSTART:{start}
DTEND:{end}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:{desc}
END:VEVENT
"""
        events.append(event)

    return "BEGIN:VCALENDAR\nVERSION:2.0\n" + "".join(events) + "END:VCALENDAR\n"

def main():
    config = yaml.safe_load(open("config.yaml"))
    csv_url = config["sheet_csv_url"]
    tz = pytz.timezone(config["timezone"])

    rows = load_sheet(csv_url)

    # Generate parents ICS
    parents_ics = generate_ics(rows, tz, "parents")
    with open("calendriers/parents_aventurier.ics", "w", encoding="utf-8") as f:
        f.write(parents_ics)

    # Generate leaders ICS
    leaders_ics = generate_ics(rows, tz, "animateurs")
    with open("calendrier/animateurs_aventurier.ics", "w", encoding="utf-8") as f:
        f.write(animateurs_ics)

if __name__ == "__main__":
    main()
