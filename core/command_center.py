from core.dispatch import DispatchEngine
from core.incident import Incident
from core.incident_manager import IncidentManager
from core.resource_manager import ResourceManager
from core import storage


class CommandCenter:
    def __init__(self):
        self.incidents = IncidentManager()
        self.resources = ResourceManager()
        self.dispatch = DispatchEngine()
        self.load_responders()
        self.load_incidents()

    def load_responders(self):
        for responder in storage.load_responders():
            self.resources.add_responder(responder)

    def load_incidents(self):
        # Everything comes from data/incidents.csv so the app has a single source of truth
        Incident.id_counter = 0  # resent counter; set_id bumps it past the loaded IDs
        for incident in storage.load_incidents():
            self.incidents.add_incident(incident)

    def add_incident(self, incident, persist=True):
        self.incidents.add_incident(incident)
        if persist:
            try:
                storage.append_incident(incident)
            except Exception as error:
                print(f"Could not save {incident.get_id()} to CSV: {error}")
                
    def assign_responder(self, incident, responder, is_greedy=False):
        return self.dispatch.assign_responder(incident, responder, is_greedy=is_greedy)

    def update_status(self, incident, target_status, responder=None):
        action = self.dispatch.update_incident_status(incident, target_status, responder)
        if target_status == "closed":
            try:
                storage.update_incident_status(incident.get_id(), "closed")
            except Exception:
                pass
        return action

    def undo(self):
        return self.dispatch.undo_last_action(
            self.incidents_by_id(), self.responders_by_id()
        )

    def incidents_by_id(self):
        return self.incidents.incidents_by_id()

    def responders_by_id(self):
        return self.resources.responders_by_id()

    def available_responders(self):
        return [r for r in self.resources.all_responders() if r.available]

    def open_incidents(self):
        return self.incidents.find_by_status("open")

    def status_counts(self):
        counts = {"open": 0, "assigned": 0, "in_progress": 0, "closed": 0}
        for incident in self.incidents.all_incidents():
            counts[incident.get_status()] = counts.get(incident.get_status(), 0) + 1
        return counts


def get_command_center():
    import streamlit as st

    if "command_center" not in st.session_state:
        st.session_state.command_center = CommandCenter()
    return st.session_state.command_center
