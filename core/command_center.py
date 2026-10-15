from datetime import datetime, timedelta

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
        self.seed_incidents()

    def load_responders(self):
        for responder in storage.load_responders():
            self.resources.add_responder(responder)

    def seed_incidents(self):
        now = datetime.now()
        samples = [
            ("fire", "Kitchen fire spreading through a residential building", now - timedelta(minutes=10), "Zone A", "Ahmed", "01012345678"),
            ("medical", "Person collapsed and needs urgent medical assistance", now - timedelta(minutes=30), "Zone C", "Mona", "01212345678"),
            ("crime", "Armed robbery reported near the shopping center", now - timedelta(minutes=60), "Zone B", "Sara", "01112345678"),
            ("accident", "Multi-car collision blocking the main road", now - timedelta(minutes=5), "Cairo", "Omar", "01512345678"),
            ("rescue", "Worker trapped under debris at a construction site", now - timedelta(minutes=90), "Zone D", "Youssef", "01098765432"),
        ]
        for incident_type, description, moment, location, name, phone in samples:
            try:
                self.incidents.add_incident(
                    Incident(incident_type, description, moment, location, name, phone)
                )
            except Exception:
                continue

    def add_incident(self, incident, persist=True):
        self.incidents.add_incident(incident)
        if persist:
            try:
                storage.append_incident(incident)
            except Exception:
                pass

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
