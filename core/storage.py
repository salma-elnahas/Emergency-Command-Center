import csv
import os
import re
from datetime import datetime

from core.responders import RESPONDER_TYPES
from core.incident import Incident, InvalidIncidentException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INCIDENTS_CSV = os.path.join(DATA_DIR, "incidents.csv")
RESPONDERS_CSV = os.path.join(DATA_DIR, "responders.csv")

INCIDENT_FIELDS = [
    "incident_id",
    "caller_phone",
    "incident_type",
    "severity_level",
    "location_zone",
    "timestamp",
    "status",
    "resolution_time_mins",
]

APP_TO_CSV_TYPE = {
    "natural disaster": "Natural Disaster",
    "fire": "Fire",
    "medical": "Medical",
    "accident": "Accident",
    "crime": "Police",
    "hazardous material": "Hazmat",
    "rescue": "Rescue",
    "infrastructure failure": "Infrastructure",
    "public disturbance": "Disturbance",
    "other": "Other",
}

APP_TO_CSV_STATUS = {
    "open": "Open",
    "assigned": "Assigned",
    "in_progress": "In Progress",
    "closed": "Closed",
}

CSV_TO_APP_TYPE = {value: key for key, value in APP_TO_CSV_TYPE.items()}
CSV_TO_APP_STATUS = {value: key for key, value in APP_TO_CSV_STATUS.items()}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


_TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%y %H:%M",
    "%m/%d/%Y",
)


def parse_timestamp(value):
    # Accept both ISO ("2026-10-14 07:15:00") and US ("10/14/2026 7:15") styles
    value = (value or "").strip()
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.now()


def load_incidents(path=INCIDENTS_CSV):
    # Rebuild Incident objects from incidents.csv, keeping saved IDs, times and statuses
    incidents = []
    if not os.path.exists(path):
        return incidents
    with open(path, newline="", encoding="utf-8") as handle:
        for line_no, row in enumerate(csv.DictReader(handle), start=2):
            try:
                csv_type = (row.get("incident_type") or "").strip()
                zone = (row.get("location_zone") or "").strip()

                # Timestamps may be missing or use a non-ISO format; parse flexibly
                moment = parse_timestamp(row.get("timestamp"))

                # The dataset may contain loosely-formatted phones; keep a valid
                # placeholder so a bad number never drops an otherwise good row
                phone = (row.get("caller_phone") or "").strip()
                if not re.match(r"^01[0125]\d{8}$", re.sub(r"[\s\-]", "", phone)):
                    phone = "01000000000"

                incident = Incident(
                    type=CSV_TO_APP_TYPE[csv_type],
                    description=f"{csv_type} incident reported in {zone}",  # not stored in the CSV
                    time=moment,
                    location=zone,
                    reporter_name="Unknown caller",  # not stored in the CSV
                    reporter_phone=phone,
                    status=CSV_TO_APP_STATUS[(row.get("status") or "").strip()],
                    id=row.get("incident_id"),
                )
                severity = (row.get("severity_level") or "").strip()
                if severity:
                    incident.set_severity(int(severity))  # keep the dataset's value
                resolution = (row.get("resolution_time_mins") or "").strip()
                if resolution:
                    try:
                        incident.resolution_time_mins = float(resolution)
                    except ValueError:
                        pass
                incidents.append(incident)
            except (KeyError, ValueError, InvalidIncidentException) as error:
                print(f"incidents.csv line {line_no} skipped: {error}")
    return incidents


def load_responders(path=RESPONDERS_CSV):
    responders = []
    if not os.path.exists(path):
        return responders
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            responder_type = (row.get("responder_type") or "").strip()
            responder_class = RESPONDER_TYPES.get(responder_type)
            if responder_class is None:
                continue
            responder_id = (row.get("responder_id") or "").strip()
            zone = (row.get("current_zone") or "Unknown").strip()
            status = (row.get("status") or "available").strip().lower()
            try:
                responders.append(responder_class(responder_id, zone, status=status))
            except Exception:
                continue
    return responders


def save_responders(responders, path=RESPONDERS_CSV):
    _ensure_data_dir()
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["responder_id", "responder_type", "current_zone", "status"],
        )
        writer.writeheader()
        for responder in responders:
            writer.writerow(responder.to_dict())


def append_incident(incident, resolution_time_mins="", path=INCIDENTS_CSV):
    _ensure_data_dir()
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INCIDENT_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "incident_id": incident.get_id(),
                "caller_phone": incident.get_reporter_phone(),
                "incident_type": APP_TO_CSV_TYPE.get(incident.get_type(), "Other"),
                "severity_level": incident.get_severity(),
                "location_zone": incident.get_location(),
                "timestamp": incident.get_time().strftime("%Y-%m-%d %H:%M:%S"),
                "status": APP_TO_CSV_STATUS.get(incident.get_status(), "Open"),
                "resolution_time_mins": resolution_time_mins,
            }
        )


def update_incident_status(incident_id, status, resolution_time_mins="", path=INCIDENTS_CSV):
    if not os.path.exists(path):
        return False
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    updated = False
    for row in rows:
        if row.get("incident_id") == incident_id:
            row["status"] = APP_TO_CSV_STATUS.get(status, row.get("status"))
            if resolution_time_mins != "":
                row["resolution_time_mins"] = resolution_time_mins
            updated = True
    if updated:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=INCIDENT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    return updated
