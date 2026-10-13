import streamlit as st
from datetime import datetime
from calculate_priority import calculate_priority
from quick_sort import random_quick_sort
def show_priority_board(manager):
    st.title("Priority Board")
    sort_by = st.sidebar.selectbox("Sort incidents by",["priority", "severity", "timestamp"])
    incidents=[]
    for incident in manager.incidents.queue:
        if incident.get_status() == "open":
            incidents.append(incident)
    if len(incidents) == 0:
        st.markdown("No open incidents waiting for assignment.")
        return
    try:
        time = incidents[0].get_time()
        now = datetime.now(tz=time.tzinfo)
        sorted_incidents, stats = random_quick_sort(incidents, now=now, sort_by=sort_by)
        data = []
        position = 1
        for incident in sorted_incidents:
            waiting_minutes = (now - incident.get_time()).total_seconds() / 60
            data.append({
                "Position": position,
                "ID": incident.get_id(),
                "Type": incident.get_type(),
                "Severity": incident.get_severity(),
                "Location": incident.get_location(),
                "Reported at": incident.get_time(),
                "Status": incident.get_status(),
                "Waiting (minutes)": round(waiting_minutes, 2),
                "Priority score": round(calculate_priority(incident, now), 2)
            })
            position += 1
    except (ValueError, TypeError, AttributeError) as error:
        st.error(f"Cannot display the Priority Board: {error}")
        return
    st.metric("Incidents waiting", len(sorted_incidents))
    st.dataframe(data, hide_index=True)
    st.button("Refresh priorities")
    st.subheader("Sorting statistics")
    comparisons_col, swaps_col, calls_col = st.columns(3)
    comparisons_col.metric("Comparisons", stats["comparisons"])
    swaps_col.metric("Swaps", stats["swaps"])
    calls_col.metric("Recursive calls", stats["recursive_calls"])
