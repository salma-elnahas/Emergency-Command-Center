from datetime import datetime


def calculate_priority(incident, now=None):
    severity = incident.get_severity()
    timestamp = incident.get_time()
    severity_txt = str(severity).strip()
    if not severity_txt.isdigit():
        raise ValueError("Severity must be a whole number from 1 to 5.")
    severity = int(severity_txt)
    if severity < 1 or severity > 5:
        raise ValueError("Severity must be a whole number from 1 to 5.")
    try:
        if now is None:
            now = datetime.now(tz=timestamp.tzinfo)
        waiting_time = (now - timestamp).total_seconds() / 60  # in mins
    except (TypeError, AttributeError):
        raise ValueError("Timestamp must be a datetime value with a compatible timezone.")
    if waiting_time < 0:
        raise ValueError("Incident timestamp cannot be in the future.")
    priority_score = severity * 100 + waiting_time * 0.5
    return priority_score
