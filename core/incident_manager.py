import re

from core.incident import Incident, InvalidIncidentException
from core.incident_queue import Queue


class IncidentManager:
    SEVERITY_LEVELS = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "low"}

    def __init__(self):
        self.incidents = Queue()

    def add_incident(self, incident):
        self.incidents.enqueue(incident)

    def remove_incident(self):
        return self.incidents.dequeue()

    def all_incidents(self):
        return self.incidents.to_list()

    def __len__(self):
        return self.incidents.size()

    def __iter__(self):
        return iter(self.incidents.to_list())

    @staticmethod
    def id_number(incident_id):
        if not isinstance(incident_id, str) or not re.match(r"^INC\d{4,}$", incident_id):
            raise InvalidIncidentException("Invalid ID format! Must be in format INCXXXX.")
        return int(incident_id[3:])

    def find_by_id(self, id):
        if id is None:
            return None
        id_number = IncidentManager.id_number(id)
        items = self.incidents.queue
        low, high = 0, len(items) - 1
        while low <= high:
            mid = (low + high) // 2
            mid_number = IncidentManager.id_number(items[mid].get_id())
            if mid_number == id_number:
                return items[mid]
            elif mid_number < id_number:
                low = mid + 1
            else:
                high = mid - 1
        return None

    def find_by_location(self, location):
        location = location.strip().lower()
        results = []
        for inc in self.incidents.queue:
            if location in inc.get_location().lower():
                results.append(inc)
        return results

    def find_by_status(self, status):
        status = status.strip().lower()
        return [inc for inc in self.incidents.queue if inc.get_status() == status]

    def incidents_by_id(self):
        return {inc.get_id(): inc for inc in self.incidents.queue}
