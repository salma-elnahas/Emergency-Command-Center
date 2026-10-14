import math
from datetime import datetime
import streamlit as st

class DispatchError(Exception):
    pass

class ResponderUnavailableError(DispatchError):   #Raised when trying to assign a responder who is not available.
    pass

class InvalidStatusTransitionError(DispatchError):   #Raised when attempting an illegal incident status change.
    pass

class EmptyStackError(DispatchError):   #Raised when attempting an undo operation on an empty history stack.
    pass

class IncompatibleResponderTypeError(DispatchError):    #Raised when responder type is strictly incompatible with incident requirements.
    pass


# ----------------------------------Stack-------------------------------------------
class ActionRecord:
    def __init__(self, action_type, incident_id, responder_id, prev_incident_status,  new_incident_status, prev_responder_status,
                 new_responder_status, description=""):
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

    def push(self, action: ActionRecord):
        self._items.append(action)

    def pop(self) -> ActionRecord:
        if self.is_empty():
            raise EmptyStackError("No actions available to undo.")
        return self._items.pop()

    def peek(self) -> ActionRecord:
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:            # return the stack depth
        return len(self._items)

    def get_all_actions(self):
        return list(reversed(self._items))


class DispatchEngine:
    VALID_TRANSITIONS = {
        "open": ["assigned"],
        "assigned": ["in_progress", "open"],
        "in_progress": ["closed", "assigned"],
        "closed": []  # Terminal state
    }

    INCIDENT_RESPONDER_MAP = {
        "Fire": ["FireTruck"],
        "Medical": ["Ambulance"],
        "Security": ["Police"],
        "Accident": ["Ambulance", "Police", "FireTruck"],
        "Hazard": ["FireTruck", "Police"]
    }

    def __init__(self, history_stack: ActionHistoryStack = None):
        self.history_stack = history_stack if history_stack else ActionHistoryStack()

    @staticmethod
    def calculate_distance(loc1: tuple, loc2: tuple) -> float:   # هنا انا بحسب المسافه بين مكان الطوارئ ومكان الحادثه
        x1, y1 = loc1
        x2, y2 = loc2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def select_best_responder_greedy(self, incident, responders_list):
        # Filter available responders
        available_responders = [r for r in responders_list if getattr(r, 'status', 'available').lower() == 'available']
        if not available_responders:
            raise ResponderUnavailableError(f"No available responders in the system for Incident #{incident['id']}.")

        # Filter by compatibility (Greedy constraint relaxation if exact type missing)
        req_types = self.INCIDENT_RESPONDER_MAP.get(incident.get('type'), [])
        compatible_responders = [
            r for r in available_responders
            if getattr(r, 'type', '') in req_types or getattr(r, 'responder_type', '') in req_types
        ]

        candidates = compatible_responders if compatible_responders else available_responders

        # Greedy choice - Pick candidate with Minimum Distance
        best_responder = None
        min_distance = float('inf')
        inc_loc = incident.get('location', (0, 0))

        for resp in candidates:
            resp_loc = getattr(resp, 'location', (0, 0))
            dist = self.calculate_distance(inc_loc, resp_loc)
            if dist < min_distance:
                min_distance = dist
                best_responder = resp

        return best_responder, round(min_distance, 2)

    def validate_transition(self, current_status: str, target_status: str):
        current_status = current_status.lower()
        target_status = target_status.lower()

        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Invalid status change: Cannot change incident status from '{current_status}' to '{target_status}'. "
                f"Allowed transitions from '{current_status}': {allowed}"
            )

    def assign_responder(self, incident: dict, responder, is_greedy: bool = False) -> ActionRecord:
        if getattr(responder, 'status', 'available').lower() != 'available':
            raise ResponderUnavailableError(f"Responder #{responder.id} is currently unavailable ({responder.status}).")

        self.validate_transition(incident['status'], 'assigned')
        prev_inc_status = incident['status']
        prev_resp_status = responder.status

        incident['status'] = 'assigned'
        incident['assigned_responder_id'] = responder.id
        responder.status = 'busy'

        desc = f"Assigned {'(Greedy)' if is_greedy else ''} Responder #{responder.id} to Incident #{incident['id']}"
        action = ActionRecord(
            action_type="ASSIGN",
            incident_id=incident['id'],
            responder_id=responder.id,
            prev_incident_status=prev_inc_status,
            new_incident_status='assigned',
            prev_responder_status=prev_resp_status,
            new_responder_status='busy',
            description=desc
        )

        self.history_stack.push(action)
        return action

    def update_incident_status(self, incident: dict, target_status: str, responder=None) -> ActionRecord:

        self.validate_transition(incident['status'], target_status)

        prev_inc_status = incident['status']
        prev_resp_status = responder.status if responder else None
        new_resp_status = prev_resp_status

        incident['status'] = target_status

        if target_status == 'closed' and responder:
            responder.status = 'available'
            new_resp_status = 'available'

        action = ActionRecord(
            action_type="STATUS_CHANGE",
            incident_id=incident['id'],
            responder_id=responder.id if responder else None,
            prev_incident_status=prev_inc_status,
            new_incident_status=target_status,
            prev_responder_status=prev_resp_status,
            new_responder_status=new_resp_status,
            description=f"Updated Incident #{incident['id']} status from '{prev_inc_status}' to '{target_status}'"
        )

        self.history_stack.push(action)
        return action

    def undo_last_action(self, incidents_dict: dict, responders_dict: dict) -> ActionRecord:
        action = self.history_stack.pop()  # Will raise EmptyStackError if stack is empty

        incident = incidents_dict.get(action.incident_id)
        responder = responders_dict.get(action.responder_id)

        if incident:
            incident['status'] = action.prev_incident_status
            if action.action_type == "ASSIGN" and action.prev_incident_status == 'open':
                incident['assigned_responder_id'] = None

        if responder and action.prev_responder_status is not None:
            responder.status = action.prev_responder_status

        return action


##############################################################
# --------------------------------------------------streamlit--------------------------------------------
def render_dispatch_page():
    st.title(" Dispatch & Tracking Command Center")
    st.caption(" Manage Status Lifecycle & Track Action History")

    if 'history_stack' not in st.session_state:
        st.session_state.history_stack = ActionHistoryStack()

    engine = DispatchEngine(st.session_state.history_stack)

    if 'incidents' not in st.session_state:
        st.session_state.incidents = {
            101: {'id': 101, 'type': 'Fire', 'severity': 'High', 'location': (2, 8), 'status': 'open',
                  'assigned_responder_id': None},
            102: {'id': 102, 'type': 'Medical', 'severity': 'Critical', 'location': (10, 12), 'status': 'open',
                  'assigned_responder_id': None},
            103: {'id': 103, 'type': 'Security', 'severity': 'Medium', 'location': (5, 3), 'status': 'assigned',
                  'assigned_responder_id': 301},
        }

    class MockResponder:
        def __init__(self, rid, rtype, loc, status="available"):
            self.id = rid
            self.type = rtype
            self.location = loc
            self.status = status

    if 'responders' not in st.session_state:
        st.session_state.responders = {
            201: MockResponder(201, "FireTruck", (3, 7), "available"),
            202: MockResponder(202, "Ambulance", (9, 11), "available"),
            203: MockResponder(203, "Ambulance", (20, 25), "available"),
            301: MockResponder(301, "Police", (5, 4), "busy"),
        }

    incidents = st.session_state.incidents
    responders = st.session_state.responders

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    open_count = sum(1 for i in incidents.values() if i['status'] == 'open')
    assigned_count = sum(1 for i in incidents.values() if i['status'] == 'assigned')
    in_prog_count = sum(1 for i in incidents.values() if i['status'] == 'in_progress')
    closed_count = sum(1 for i in incidents.values() if i['status'] == 'closed')

    col_m1.metric("Open Incidents", open_count, delta_color="inverse")
    col_m2.metric("Assigned", assigned_count)
    col_m3.metric("In Progress", in_prog_count)
    col_m4.metric("Closed", closed_count)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([" Intelligent Dispatch", " Status Lifecycle Workflow", " Action History & Undo"])

    with tab1:
        st.subheader("Greedy Automatic & Manual Responder Assignment")

        open_incidents = [i for i in incidents.values() if i['status'] == 'open']

        if not open_incidents:
            st.success(" No open incidents requiring assignment at this moment.")
        else:
            selected_inc_id = st.selectbox(
                "Select Open Incident to Assign:",
                options=[i['id'] for i in open_incidents],
                format_func=lambda
                    x: f"Incident #{x} - {incidents[x]['type']} ({incidents[x]['severity']} Priority) @ Location {incidents[x]['location']}"
            )

            selected_incident = incidents[selected_inc_id]

            col_a1, col_a2 = st.columns(2)

            with col_a1:
                st.markdown("#####  Smart Auto-Dispatch (Greedy Algorithm)")
                st.write("Uses Greedy Logic to find nearest compatible & available unit.")

                if st.button("Run Greedy Recommendation & Assign", type="primary"):
                    try:
                        best_resp, dist = engine.select_best_responder_greedy(
                            selected_incident, list(responders.values())
                        )
                        action = engine.assign_responder(selected_incident, best_resp, is_greedy=True)
                        st.success(
                            f" Greedy Match Success! Assigned **{best_resp.type} #{best_resp.id}** (Distance: {dist} units).")
                        st.rerun()
                    except DispatchError as e:
                        st.error(f" Dispatch Error: {str(e)}")

            with col_a2:
                st.markdown("#####  Manual Dispatch")
                available_resps = [r for r in responders.values() if r.status == 'available']

                if not available_resps:
                    st.warning("No responders currently available for manual assignment.")
                else:
                    manual_resp_id = st.selectbox(
                        "Choose Available Responder:",
                        options=[r.id for r in available_resps],
                        format_func=lambda x: f"Responder #{x} - {responders[x].type} @ {responders[x].location}"
                    )

                    if st.button("Assign Selected Responder Manually"):
                        try:
                            resp_obj = responders[manual_resp_id]
                            action = engine.assign_responder(selected_incident, resp_obj, is_greedy=False)
                            st.success(
                                f" Manually assigned Responder #{manual_resp_id} to Incident #{selected_inc_id}.")
                            st.rerun()
                        except DispatchError as e:
                            st.error(f" Exception Caught: {str(e)}")


    with tab2:
        st.subheader("Lifecycle Status Tracking (open ➔ assigned ➔ in_progress ➔ closed)")
        active_inc_ids = list(incidents.keys())
        if not active_inc_ids:
            st.info("No active incidents found.")
        else:
            inc_id = st.selectbox("Select Incident to Update:", options=active_inc_ids)
            inc = incidents[inc_id]

            st.info(
                f"Current Status of Incident #{inc_id}: **{inc['status'].upper()}** | Assigned Unit: **{inc['assigned_responder_id']}**")

            st.write("Advance Incident to Next Lifecycle State:")
            col_b1, col_b2, col_b3 = st.columns(3)

            with col_b1:
                if st.button("Mark as IN_PROGRESS"):
                    try:
                        resp_obj = responders.get(inc['assigned_responder_id'])
                        engine.update_incident_status(inc, "in_progress", resp_obj)
                        st.success(f"Incident #{inc_id} marked as IN_PROGRESS.")
                        st.rerun()
                    except InvalidStatusTransitionError as e:
                        st.error(f"Lifecycle Constraint Violation: {str(e)}")

            with col_b2:
                if st.button("Mark as CLOSED (Resolve)"):
                    try:
                        resp_obj = responders.get(inc['assigned_responder_id'])
                        engine.update_incident_status(inc, "closed", resp_obj)
                        st.success(
                            f"Incident #{inc_id} CLOSED! Responder #{inc['assigned_responder_id']} released to Available.")
                        st.rerun()
                    except InvalidStatusTransitionError as e:
                        st.error(f"️ Lifecycle Constraint Violation: {str(e)}")

            with col_b3:
                if st.button(" Try Invalid Jump to CLOSED (Error Demo)"):
                    try:
                        engine.validate_transition(inc['status'], "closed")
                    except InvalidStatusTransitionError as e:
                        st.error(f" Custom Exception Triggered Correctly:\n{str(e)}")

    with tab3:
        st.subheader("Action Log & Stack Undo Control")
        st.write("Demonstrating custom LIFO Stack data structure for command rollback.")

        col_u1, col_u2 = st.columns([1, 3])

        with col_u1:
            st.metric("Stack Depth", st.session_state.history_stack.size())

            if st.button(" UNDO LAST ACTION", type="secondary", use_container_width=True):
                try:
                    undone_action = engine.undo_last_action(incidents, responders)
                    st.warning(f" Undone Action: {undone_action.description}")
                    st.rerun()
                except EmptyStackError as e:
                    st.error(f" Stack Underflow Error: {str(e)}")

        with col_u2:
            st.markdown("##### Stack Audit Trail (Newest First)")
            actions = st.session_state.history_stack.get_all_actions()

            if not actions:
                st.text("No history recorded in Stack yet.")
            else:
                for idx, act in enumerate(actions):
                    st.code(
                        f"[{idx + 1}] Timestamp: {act.timestamp}\n"
                        f"    Type: {act.action_type}\n"
                        f"    Description: {act.description}\n"
                        f"    Incident Status Change: {act.prev_incident_status} ➔ {act.new_incident_status}\n"
                        f"    Responder Status Change: {act.prev_responder_status} ➔ {act.new_responder_status}",
                        language="text"
                    )


if __name__ == "__main__":
    st.set_page_config(page_title="Dispatch & Tracking Module", layout="wide")
    render_dispatch_page()




