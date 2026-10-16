import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Dispatch & Tracking", page_icon="🚑", layout="wide")

from core.command_center import get_command_center
from core.dispatch import (
    DispatchError,
    EmptyStackError,
    InvalidStatusTransitionError,
)

st.title("Dispatch & Tracking Command Center")
st.caption("Manage the incident status lifecycle and track the action history stack.")

cc = get_command_center()
engine = cc.dispatch
history = engine.history_stack
incidents = cc.incidents_by_id()
responders = cc.responders_by_id()

counts = cc.status_counts()
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Open Incidents", counts["open"], delta_color="inverse")
col_m2.metric("Assigned", counts["assigned"])
col_m3.metric("In Progress", counts["in_progress"])
col_m4.metric("Closed", counts["closed"])

st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["Intelligent Dispatch", "Status Lifecycle Workflow", "Action History & Undo"]
)

with tab1:
    st.subheader("Greedy automatic & manual responder assignment")

    open_incidents = list(cc.open_incidents())
    if not open_incidents:
        st.success("No open incidents requiring assignment at this moment.")
    else:
        selected_inc_id = st.selectbox(
            "Select open incident to assign:",
            options=[inc.get_id() for inc in open_incidents],
            format_func=lambda x: (
                f"Incident #{x} - {incidents[x].get_type()} "
                f"(severity {incidents[x].get_severity()}) @ {incidents[x].get_location()}"
            ),
        )
        selected_incident = incidents[selected_inc_id]

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown("##### Smart auto-dispatch (greedy)")
            st.write("Picks the nearest compatible and available unit.")
            if st.button("Run greedy recommendation & assign", type="primary"):
                try:
                    best_resp, dist = engine.select_best_responder_greedy(
                        selected_incident, cc.resources.all_responders()
                    )
                    engine.assign_responder(selected_incident, best_resp, is_greedy=True)
                    st.success(
                        f"Assigned {best_resp.type} #{best_resp.responder_id} "
                        f"(distance {dist} units)."
                    )
                    st.rerun()
                except DispatchError as error:
                    st.error(f"Dispatch error: {error}")

with tab2:
    st.subheader("Lifecycle status tracking (open -> assigned -> in_progress -> closed)")
    if not incidents:
        st.info("No incidents found.")
    else:
        status_filter = st.selectbox(
            "Filter incidents by status:",
            options=["All", "open", "assigned", "in_progress", "closed"],
            format_func=lambda value: (
                "All statuses" if value == "All" else value.replace("_", " ").upper()
            ),
        )
        filtered_ids = [
            incident_id
            for incident_id, incident in incidents.items()
            if status_filter == "All" or incident.get_status() == status_filter
        ]

        if not filtered_ids:
            st.info(f"No incidents with status '{status_filter}'.")
        else:
            inc_id = st.selectbox("Select incident to update:", options=filtered_ids)
            inc = incidents[inc_id]
            st.info(
                f"Current status of incident #{inc_id}: **{inc.get_status().upper()}** | "
                f"Assigned unit: **{inc.assigned_responder_id}**"
            )

            assigned_resp = responders.get(inc.assigned_responder_id) if inc.assigned_responder_id else None

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("Mark as IN_PROGRESS"):
                    try:
                        engine.update_incident_status(inc, "in_progress", assigned_resp)
                        st.success(f"Incident #{inc_id} marked as in progress.")
                        st.rerun()
                    except InvalidStatusTransitionError as error:
                        st.error(f"Lifecycle constraint violation: {error}")
            with col_b2:
                if st.button("Mark as CLOSED (resolve)"):
                    try:
                        cc.update_status(inc, "closed", assigned_resp)
                        st.success(f"Incident #{inc_id} closed. Responder released.")
                        st.rerun()
                    except InvalidStatusTransitionError as error:
                        st.error(f"Lifecycle constraint violation: {error}")

with tab3:
    st.subheader("Action log & stack undo control")
    st.write("Demonstrates a custom LIFO stack for command rollback.")

    col_u1, col_u2 = st.columns([1, 3])
    with col_u1:
        st.metric("Stack depth", history.size())
        if st.button("UNDO LAST ACTION", type="secondary", width='stretch'):
            try:
                undone = cc.undo()
                st.warning(f"Undone action: {undone.description}")
                st.rerun()
            except EmptyStackError as error:
                st.error(f"Stack underflow error: {error}")

    with col_u2:
        st.markdown("##### Stack audit trail (newest first)")
        actions = history.get_all_actions()
        if not actions:
            st.text("No history recorded in the stack yet.")
        else:
            for idx, act in enumerate(actions):
                st.code(
                    f"[{idx + 1}] Timestamp: {act.timestamp}\n"
                    f"    Type: {act.action_type}\n"
                    f"    Description: {act.description}\n"
                    f"    Incident Status Change: {act.prev_incident_status} -> {act.new_incident_status}\n"
                    f"    Responder Status Change: {act.prev_responder_status} -> {act.new_responder_status}",
                    language="text",
                )
