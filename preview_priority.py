import streamlit as st
from datetime import datetime, timedelta
from incident import Incident
from incident_manager import IncidentManager
from priority_board import show_priority_board


# Keep the manager between Streamlit reruns.
if "preview_manager" not in st.session_state:
    manager = IncidentManager()
    now = datetime.now()

    manager.add_incident(Incident(
        type="fire",
        description="Fire reported inside a residential building",
        time=now - timedelta(minutes=10),
        location="Cairo",
        reporter_name="Ahmed",
        reporter_phone="01012345678",
    ))

    manager.add_incident(Incident(
        type="crime",
        description="Crime reported near the shopping center",
        time=now - timedelta(minutes=60),
        location="Giza",
        reporter_name="Sara",
        reporter_phone="01112345678",
    ))

    manager.add_incident(Incident(
        type="medical",
        description="Person needs urgent medical assistance",
        time=now - timedelta(minutes=30),
        location="Alexandria",
        reporter_name="Mona",
        reporter_phone="01212345678",
    ))

    st.session_state["preview_manager"] = manager


show_priority_board(st.session_state["preview_manager"])