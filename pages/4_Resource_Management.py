import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Resource Management", page_icon="🧰", layout="wide")

from core.responders import RESPONDER_TYPES
from core.command_center import get_command_center
from core import storage

st.title("Resource Management")
st.caption("Manage responders using a custom hash table and binary search.")

cc = get_command_center()
manager = cc.resources

responders = manager.all_responders()
total = len(responders)
available = len(cc.available_responders())
col1, col2, col3 = st.columns(3)
col1.metric("Total responders", total)
col2.metric("Available", available)
col3.metric("Unavailable", total - available)

st.markdown("---")
st.subheader("Responder roster")

filter_col1, filter_col2 = st.columns(2)
type_filter = filter_col1.selectbox("Filter by type", ["All", *sorted(RESPONDER_TYPES.keys())])
availability_filter = filter_col2.selectbox("Filter by availability", ["All", "Available", "Unavailable"])

filtered = manager.filter_responders(type_filter, availability_filter)
if filtered:
    st.dataframe(
        [
            {
                "ID": r.responder_id,
                "Type": r.responder_type,
                "Zone": r.location,
                "Status": r.get_status(),
            }
            for r in filtered
        ],
        hide_index=True,
    )
else:
    st.info("No responders match the selected filters.")

st.markdown("---")
st.subheader("Add responder")
with st.form("add_responder", clear_on_submit=True):
    col_id, col_type = st.columns(2)
    responder_id = col_id.text_input("Responder ID", placeholder="AMB-004")
    responder_type = col_type.selectbox("Type", sorted(RESPONDER_TYPES.keys()))
    col_zone, col_status = st.columns(2)
    zone = col_zone.text_input("Zone", placeholder="Zone A")
    status = col_status.selectbox("Status", ["available", "busy", "offline"])
    add_submitted = st.form_submit_button("Add responder")

if add_submitted:
    if not responder_id.strip() or not zone.strip():
        st.error("Responder ID and zone are required.")
    else:
        responder_class = RESPONDER_TYPES[responder_type]
        responder = responder_class(responder_id.strip(), zone.strip(), status=status)
        if manager.add_responder(responder):
            storage.save_responders(manager.all_responders())
            st.success(f"Added {responder.responder_type} {responder.responder_id}.")
            st.rerun()
        else:
            st.error(f"Responder {responder_id} already exists.")

st.markdown("---")
st.subheader("Update or remove")
if responders:
    selected_id = st.selectbox("Select responder", [r.responder_id for r in responders])
    selected = manager.find_by_id(selected_id)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_status = st.selectbox(
            "Set status", ["available", "busy", "offline"], index=["available", "busy", "offline"].index(selected.status)
        )
        if st.button("Update status"):
            selected.set_status(new_status)
            storage.save_responders(manager.all_responders())
            st.success(f"{selected_id} set to {new_status}.")
            st.rerun()
    with col_b:
        st.write("Hash lookup")
        st.code(f"find_by_id({selected_id}) -> {manager.find_by_id(selected_id)!r}", language="text")
    with col_c:
        if st.button("Remove responder"):
            manager.remove_responder(selected_id)
            storage.save_responders(manager.all_responders())
            st.warning(f"Removed {selected_id}.")
            st.rerun()
else:
    st.info("No responders registered.")
