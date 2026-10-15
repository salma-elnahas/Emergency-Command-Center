import os
import sys
from datetime import datetime, date, time as dt_time

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Incident Intake", page_icon="📝", layout="wide")

from core.incident import Incident, InvalidIncidentException
from core.command_center import get_command_center

st.title("Incident Intake")
st.caption("Register a new incident. All fields are validated before it enters the queue.")

cc = get_command_center()

with st.form("incident_form", clear_on_submit=True):
    incident_type = st.selectbox("Incident type", sorted(Incident.TYPE_SEVERITY.keys()))

    description = st.text_area(
        "Description", max_chars=250, placeholder="Describe the emergency (5-250 characters)"
    )

    location = st.text_input("Location", placeholder="e.g. Zone A, Cairo")

    col_date, col_time = st.columns(2)
    reported_date = col_date.date_input("Reported date", value=date.today())
    reported_time = col_time.time_input("Reported time", value=dt_time(0, 0))

    col_name, col_phone = st.columns(2)
    reporter_name = col_name.text_input("Reporter name")
    reporter_phone = col_phone.text_input("Reporter phone", placeholder="01xxxxxxxxx")

    submitted = st.form_submit_button("Register incident", type="primary")

if submitted:
    reported_at = datetime.combine(reported_date, reported_time)
    try:
        incident = Incident(
            type=incident_type,
            description=description,
            time=reported_at,
            location=location,
            reporter_name=reporter_name,
            reporter_phone=reporter_phone,
        )
    except InvalidIncidentException as error:
        st.error(f"Invalid incident: {error}")
    else:
        cc.add_incident(incident)
        st.success(
            f"Incident {incident.get_id()} registered and queued with severity {incident.get_severity()}."
        )

st.markdown("---")
st.subheader("Registered incidents")
incidents = cc.incidents.all_incidents()
if incidents:
    st.dataframe(
        [
            {
                "ID": incident.get_id(),
                "Type": incident.get_type(),
                "Severity": incident.get_severity(),
                "Location": incident.get_location(),
                "Reported at": incident.get_time(),
                "Status": incident.get_status(),
            }
            for incident in reversed(incidents)
        ],
        hide_index=True,
    )
else:
    st.info("No incidents registered yet.")
