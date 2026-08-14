import csv
import requests
import yaml
from datetime import datetime
from zoneinfo import ZoneInfo
import io
import re

def load_sheet(csv_url):
    r = requests.get(csv_url)
    r.raise_for_status()
    f = io.StringIO(r.content.decode("utf-8"))
    rows = list(csv.DictReader(f))
    return rows

def to_dt(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=ZoneInfo("America/Toronto"))
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")  

def escape_description(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\\n")

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def fold_ics_line(line):
    folded = []
    for i in range(0, len(line), 73):
        folded.append(line[i:i+73])
    return "\r\n ".join(folded)

def build_description(row, audience):
    parent_desc = escape_description(row["Description (Parents)"].strip())
    anim_desc = escape_description(row["Description (Animateurs)"].strip())
    if audience == "parents":
        return parent_desc
    parts = []
    if parent_desc:
        parts.append(parent_desc)
    if anim_desc:
        parts.append(anim_desc)
    return "\\n".join(parts)

def generate_ics(rows, audience):
    events = []

    for row in rows:
        parent_desc = row["Description (Parents)"].strip()
        if audience == "parents" and not parent_desc:
            continue
        start_date = row["Start_Date"].strip()
        start_time = row["Start_Time"].strip()
        end_date = row["End_Date"].strip() if row["End_Date"].strip() else start_date
        end_time = row["End_Time"].strip()
        
        start = to_dt(start_date, start_time)
        end = to_dt(end_date, end_time)
        dtstamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")

        desc = build_description(row, audience)
        title = row["Title"]
        location = row["Location"]
        uid = f"{audience}-{start_date.replace('-', '')}-{slugify(title)}"

        event = []
        event.append("BEGIN:VEVENT")
        event.append(fold_ics_line(f"UID:{uid}"))
        event.append(fold_ics_line(f"DTSTAMP:{dtstamp}"))
        event.append(fold_ics_line(f"DTSTART:{start}"))
        event.append(fold_ics_line(f"DTEND:{end}"))
        event.append(fold_ics_line(f"SUMMARY:{title}"))
        event.append(fold_ics_line(f"LOCATION:{location}"))
        event.append(fold_ics_line(f"DESCRIPTION:{desc}"))
        event.append("END:VEVENT")

        events.append("\n".join(event))

        ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "PRODID:-//calendrier_scout//EN"
        ]
        ics.extend(events)
        ics.append("END:VCALENDAR")

    return "\n".join(ics)

def main():
    config = yaml.safe_load(open("config.yaml"))
    csv_url = config["sheet_csv_url"]

    rows = load_sheet(csv_url)

    parents_ics = generate_ics(rows, "parents")
    with open("calendriers/parents_aventurier.ics", "w", encoding="utf-8") as f:
        f.write(parents_ics)

    animateurs_ics = generate_ics(rows, "animateurs")
    with open("calendriers/animateurs_aventurier.ics", "w", encoding="utf-8") as f:
        f.write(animateurs_ics)

if __name__ == "__main__":
    main()
