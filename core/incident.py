from datetime import datetime
import re


class InvalidIncidentException(Exception):
    pass


class Incident:
    VALID_STATUSES = ["open", "assigned", "in_progress", "closed"]
    TYPE_SEVERITY = {
        "natural disaster": 5,
        "fire": 5,
        "medical": 5,
        "accident": 4,
        "crime": 4,
        "hazardous material": 4,
        "rescue": 4,
        "infrastructure failure": 3,
        "public disturbance": 2,
        "other": 1,
    }

    id_counter = 0

    def __init__(self, type, description, time, location, reporter_name, reporter_phone, status="open", id=None):
        self.set_type(type)
        self.set_description(description)
        self.set_time(time)
        self.set_location(location)
        self.set_reporter_name(reporter_name)
        self.set_reporter_phone(reporter_phone)
        self.set_status(status)
        self.assigned_responder_id = None
        self.resolution_time_mins = None
        if id is None:
            # new incident: generate a fresh ID
            Incident.id_counter += 1
            self.id = f"INC{Incident.id_counter:04d}"
        else:
            # incident loaded from storage: restore its saved ID
            self.set_id(id)

    # Setters

    def set_id(self, id):
        if not isinstance(id, str):
            raise InvalidIncidentException("ID must look like INC0001.")
        cleaned = id.strip().upper()
        match = re.match(r"^INC-?(\d{4,})$", cleaned)
        if not match:
            raise InvalidIncidentException("ID must look like INC0001.")
        self.id = cleaned
        # Keep the counter ahead of every ID that already exists
        Incident.id_counter = max(Incident.id_counter, int(match.group(1)))

    def set_type(self, type):
        if not isinstance(type, str):
            raise InvalidIncidentException("Invalid Type Input! Enter a text input.")
        cleaned = type.strip().lower()
        if cleaned not in Incident.TYPE_SEVERITY:
            raise InvalidIncidentException(
                f" Incident Type must be one of: {', '.join(Incident.TYPE_SEVERITY.keys())}."
            )
        self.type = cleaned
        self.severity = Incident.TYPE_SEVERITY[cleaned]

    def set_description(self, description):
        if not isinstance(description, str):
            raise InvalidIncidentException("Invalid Description Input! Enter a text input.")
        cleaned = description.strip()
        if not cleaned or len(cleaned) < 5 or len(cleaned) > 250:
            raise InvalidIncidentException("Description must be between 5 and 250 characters long.")
        self.description = cleaned

    def set_severity(self, severity):
        if not isinstance(severity, int) or not 1 <= severity <= 5:
            raise InvalidIncidentException("Severity must be an integer from 1 to 5.")
        self.severity = severity

    def set_time(self, time):
        if not isinstance(time, datetime):
            raise InvalidIncidentException("Invalid Time Input! Enter a valid date and time.")
        if time > datetime.now():
            raise InvalidIncidentException("Invalid Time Input! Enter a Valid date.")
        self.time = time

    def set_location(self, location):
        if not isinstance(location, str):
            raise InvalidIncidentException("Invalid Location Input! Enter a text input.")
        cleaned = location.strip()
        if not cleaned or len(cleaned) < 3 or len(cleaned) > 50:
            raise InvalidIncidentException("Location must be between 3 and 50 characters long.")
        self.location = cleaned

    def set_reporter_name(self, reporter_name):
        if not isinstance(reporter_name, str):
            raise InvalidIncidentException("Invalid Input! Enter a text input.")
        cleaned = reporter_name.strip()
        if not cleaned or len(cleaned) < 2 or len(cleaned) > 50:
            raise InvalidIncidentException("Reporter name must be between 2 and 50 characters long.")
        self.reporter_name = cleaned

    def set_reporter_phone(self, reporter_phone):
        if not isinstance(reporter_phone, str):
            raise InvalidIncidentException("Invalid Input! Enter a text input.")
        cleaned_phone = re.sub(r"[\s\-]", "", reporter_phone.strip())
        phone_patterns = r"^01[0125]\d{8}$"
        if not re.match(phone_patterns, cleaned_phone):
            raise InvalidIncidentException(
                "Invalid phone number format! Must be a valid 11-digit mobile number (e.g., 01012345678)."
            )
        self.reporter_phone = cleaned_phone

    def set_status(self, status):
        if isinstance(status, str):
            status = status.strip().lower().replace(" ", "_")
        if not isinstance(status, str) or status not in Incident.VALID_STATUSES:
            raise InvalidIncidentException(
                f"Status must be one of: {', '.join(Incident.VALID_STATUSES)}."
            )
        self.status = status

    # Getters

    def get_id(self):
        return self.id

    def get_type(self):
        return self.type

    def get_description(self):
        return self.description

    def get_severity(self):
        return self.severity

    def get_time(self):
        return self.time

    def get_location(self):
        return self.location

    def get_reporter_name(self):
        return self.reporter_name

    def get_reporter_phone(self):
        return self.reporter_phone

    def get_status(self):
        return self.status

    def is_open(self):
        return self.status == "open"

    def __str__(self):
        return f"[{self.id}] {self.type} | severity {self.severity} | {self.location} | {self.status}"
