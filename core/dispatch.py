import math
from datetime import datetime


class DispatchError(Exception):
    pass


class ResponderUnavailableError(DispatchError):
    pass


class InvalidStatusTransitionError(DispatchError):
    pass


class EmptyStackError(DispatchError):
    pass


class IncompatibleResponderTypeError(DispatchError):
    pass


class ActionRecord:
    def __init__(
        self,
        action_type,
        incident_id,
        responder_id,
        prev_incident_status,
        new_incident_status,
        prev_responder_status,
        new_responder_status,
        description="",
    ):
        self.action_type = action_type
        self.incident_id = incident_id
        self.responder_id = responder_id
        self.prev_incident_status = prev_incident_status
        self.new_incident_status = new_incident_status
        self.prev_responder_status = prev_responder_status
        self.new_responder_status = new_responder_status
        self.description = description
        self.timestamp = datetime.now().strftime("%H:%M:%S")

    def __repr__(self):
        return f"[{self.timestamp}] {self.action_type}: {self.description}"


class ActionHistoryStack:
    def __init__(self):
        self._items = []

    def push(self, action):
        self._items.append(action)

    def pop(self):
        if self.is_empty():
            raise EmptyStackError("No actions available to undo.")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def get_all_actions(self):
        return list(reversed(self._items))


class DispatchEngine:
    VALID_TRANSITIONS = {
        "open": ["assigned"],
        "assigned": ["in_progress", "open"],
        "in_progress": ["closed", "assigned"],
        "closed": [],
    }

    INCIDENT_RESPONDER_MAP = {
        "natural disaster": ["FireTruck", "Ambulance", "Police", "Rescue"],
        "fire": ["FireTruck", "Ambulance"],
        "medical": ["Ambulance"],
        "accident": ["Ambulance", "Police", "FireTruck"],
        "crime": ["Police"],
        "hazardous material": ["Hazmat", "FireTruck", "Police"],
        "rescue": ["Rescue", "FireTruck", "Ambulance"],
        "infrastructure failure": ["FireTruck", "Police"],
        "public disturbance": ["Police"],
        "other": [],
    }

    LOCATION_COORDS = {
        "zone a": (0.0, 0.0),
        "zone b": (4.0, 0.0),
        "zone c": (0.0, 4.0),
        "zone d": (4.0, 4.0),
        "cairo": (1.0, 1.0),
        "giza": (2.0, 3.0),
        "alexandria": (5.0, 6.0),
    }

    def __init__(self, history_stack=None):
        self.history_stack = history_stack if history_stack else ActionHistoryStack()

    @staticmethod
    def location_point(location):
        if isinstance(location, (tuple, list)) and len(location) >= 2:
            return float(location[0]), float(location[1])
        key = str(location).strip().lower()
        if key in DispatchEngine.LOCATION_COORDS:
            return DispatchEngine.LOCATION_COORDS[key]
        digest = sum(ord(character) for character in key) if key else 0
        return float(digest % 10), float((digest // 10) % 10)

    @staticmethod
    def calculate_distance(loc1, loc2):
        x1, y1 = loc1
        x2, y2 = loc2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def compatible_types(self, incident_type):
        return self.INCIDENT_RESPONDER_MAP.get(str(incident_type).strip().lower(), [])

    def select_best_responder_greedy(self, incident, responders_list):
        available_responders = [r for r in responders_list if r.available]
        if not available_responders:
            raise ResponderUnavailableError(
                f"No available responders in the system for Incident #{incident.get_id()}."
            )

        req_types = self.compatible_types(incident.get_type())
        compatible_responders = [r for r in available_responders if r.type in req_types]
        candidates = compatible_responders if compatible_responders else available_responders

        best_responder = None
        min_distance = float("inf")
        inc_point = self.location_point(incident.get_location())

        for resp in candidates:
            dist = self.calculate_distance(inc_point, self.location_point(resp.location))
            if dist < min_distance:
                min_distance = dist
                best_responder = resp

        return best_responder, round(min_distance, 2)

    def get_compatible_responders(self, incident, responders_list):
        available_responders = [r for r in responders_list if getattr(r, "available", False)]
        req_types = self.compatible_types(incident.get_type())
        compatible = [r for r in available_responders if getattr(r, "type", None) in req_types]
        return compatible

    def validate_transition(self, current_status, target_status):
        current_status = str(current_status).strip().lower().replace(" ", "_")
        target_status = str(target_status).strip().lower().replace(" ", "_")
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Invalid status change: Cannot change incident status from '{current_status}' "
                f"to '{target_status}'. Allowed transitions from '{current_status}': {allowed}"
            )

    def assign_responder(self, incident, responder, is_greedy=False):
        if not responder.available:
            raise ResponderUnavailableError(
                f"Responder #{responder.responder_id} is currently unavailable ({responder.get_status()})."
            )

        self.validate_transition(incident.get_status(), "assigned")
        prev_inc_status = incident.get_status()
        prev_resp_status = responder.status

        incident.set_status("assigned")
        incident.assigned_responder_id = responder.responder_id
        responder.status = "busy"

        desc = (
            f"Assigned {'(Greedy) ' if is_greedy else ''}Responder #{responder.responder_id} "
            f"to Incident #{incident.get_id()}"
        )
        action = ActionRecord(
            action_type="ASSIGN",
            incident_id=incident.get_id(),
            responder_id=responder.responder_id,
            prev_incident_status=prev_inc_status,
            new_incident_status="assigned",
            prev_responder_status=prev_resp_status,
            new_responder_status="busy",
            description=desc,
        )
        self.history_stack.push(action)
        return action

    def update_incident_status(self, incident, target_status, responder=None):
        self.validate_transition(incident.get_status(), target_status)

        prev_inc_status = incident.get_status()
        prev_resp_status = responder.status if responder else None
        new_resp_status = prev_resp_status

        incident.set_status(target_status)

        if target_status == "closed" and responder:
            responder.status = "available"
            new_resp_status = "available"

        action = ActionRecord(
            action_type="STATUS_CHANGE",
            incident_id=incident.get_id(),
            responder_id=responder.responder_id if responder else None,
            prev_incident_status=prev_inc_status,
            new_incident_status=target_status,
            prev_responder_status=prev_resp_status,
            new_responder_status=new_resp_status,
            description=(
                f"Updated Incident #{incident.get_id()} status from "
                f"'{prev_inc_status}' to '{target_status}'"
            ),
        )
        self.history_stack.push(action)
        return action

    def undo_last_action(self, incidents_dict, responders_dict):
        action = self.history_stack.pop()
        incident = incidents_dict.get(action.incident_id)
        responder = responders_dict.get(action.responder_id) if action.responder_id else None

        if incident:
            incident.set_status(action.prev_incident_status)
            if action.action_type == "ASSIGN" and action.prev_incident_status == "open":
                incident.assigned_responder_id = None

        if responder and action.prev_responder_status is not None:
            responder.status = action.prev_responder_status

        return action
