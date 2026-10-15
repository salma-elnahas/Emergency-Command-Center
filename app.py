import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Emergency Command Center",
    page_icon="🚨",
    layout="wide",
)

from core.command_center import get_command_center
from core.incident import Incident

st.title("Emergency Command Center")
st.caption("A unified operations console for incidents, resources and dispatch.")

cc = get_command_center()
counts = cc.status_counts()

total_col, open_col, assigned_col, progress_col, closed_col = st.columns(5)
total_col.metric("Total incidents", len(cc.incidents))
open_col.metric("Open", counts["open"])
assigned_col.metric("Assigned", counts["assigned"])
progress_col.metric("In progress", counts["in_progress"])
closed_col.metric("Closed", counts["closed"])

st.markdown("---")
st.subheader("Live resources")
available = len(cc.available_responders())
total_resources = len(cc.resources)
res_col1, res_col2 = st.columns(2)
res_col1.metric("Available responders", available)
res_col2.metric("Total responders", total_resources)

st.markdown("---")
st.subheader("Modules")
st.markdown(
    """
    - **Incident Intake** - validate and register new incidents into the live queue.
    - **Priority Board** - rank open incidents with a randomized quick sort.
    - **Dispatch & Tracking** - greedy responder assignment, status lifecycle and undo.
    - **Resource Management** - manage responders with a custom hash table.
    - **Analytics Dashboard** - historical KPIs, charts and a live zone map.
    """
)

st.markdown("---")
st.subheader("Recent incidents")
recent = cc.incidents.all_incidents()[-5:]
if recent:
    st.dataframe(
        [
            {
                "ID": incident.get_id(),
                "Type": incident.get_type(),
                "Severity": incident.get_severity(),
                "Location": incident.get_location(),
                "Status": incident.get_status(),
            }
            for incident in reversed(recent)
        ],
        hide_index=True,
    )
else:
    st.info("No incidents registered yet.")

st.caption(f"Incident types supported: {', '.join(Incident.TYPE_SEVERITY.keys())}")
