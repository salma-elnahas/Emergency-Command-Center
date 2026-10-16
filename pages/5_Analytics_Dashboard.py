import os
import sys
from datetime import date

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Analytics Dashboard", page_icon="📈", layout="wide")

from core.command_center import get_command_center
from core.storage import APP_TO_CSV_STATUS


class EmergencyDashboard:
    INCIDENT_COLUMNS = [
        "incident_id",
        "caller_phone",
        "incident_type",
        "severity_level",
        "location_zone",
        "timestamp",
        "status",
        "resolution_time_mins",
    ]
    RESPONDER_COLUMNS = ["responder_id", "responder_type", "current_zone", "status"]

    def load_data(self):
        # Use the same shared CommandCenter as every other page so the whole
        # app reads from data/incidents.csv and data/responders.csv consistently.
        cc = get_command_center()

        incidents = pd.DataFrame(
            [
                {
                    "incident_id": incident.get_id(),
                    "caller_phone": incident.get_reporter_phone(),
                    "incident_type": incident.get_type(),
                    "severity_level": incident.get_severity(),
                    "location_zone": incident.get_location(),
                    "timestamp": incident.get_time(),
                    "status": APP_TO_CSV_STATUS.get(incident.get_status(), incident.get_status()),
                    "resolution_time_mins": getattr(incident, "resolution_time_mins", None),
                }
                for incident in cc.incidents.all_incidents()
            ],
            columns=self.INCIDENT_COLUMNS,
        )
        responders = pd.DataFrame(
            [
                {
                    "responder_id": responder.responder_id,
                    "responder_type": responder.responder_type,
                    "current_zone": responder.location,
                    "status": responder.get_status(),
                }
                for responder in cc.resources.all_responders()
            ],
            columns=self.RESPONDER_COLUMNS,
        )

        if incidents.empty or responders.empty:
            st.info("No data available in the data directory yet.")
            return incidents, responders

        incidents["timestamp"] = pd.to_datetime(incidents["timestamp"], errors="coerce")
        incidents["resolution_time_mins"] = pd.to_numeric(
            incidents["resolution_time_mins"], errors="coerce"
        )
        incidents["severity_level"] = (
            pd.to_numeric(incidents["severity_level"], errors="coerce").fillna(0).astype(int)
        )
        incidents["caller_phone"] = incidents["caller_phone"].fillna("Unknown")
        incidents["status"] = incidents["status"].fillna("Unknown").str.strip().str.capitalize()

        responders["status"] = responders["status"].fillna("Unknown").str.strip().str.capitalize()
        responders["current_zone"] = responders["current_zone"].fillna("Unknown").str.strip()

        return incidents, responders

    def apply_filters(self, df):
        st.sidebar.header("Filters")

        min_date = df["timestamp"].min().date() if not df["timestamp"].dropna().empty else date.today()
        max_date = df["timestamp"].max().date() if not df["timestamp"].dropna().empty else date.today()

        date_range = st.sidebar.date_input(
            "Date Range", [min_date, max_date]
        )

        inc_types = st.sidebar.multiselect("Incident Type", options=df["incident_type"].dropna().unique())
        severities = st.sidebar.multiselect("Severity Level", options=sorted(df["severity_level"].unique()))
        zones = st.sidebar.multiselect("Location Zone", options=sorted(df["location_zone"].dropna().unique()))
        statuses = st.sidebar.multiselect("Incident Status", options=df["status"].unique())

        filtered_df = df.copy()

        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df["timestamp"].dt.date >= start_date)
                & (filtered_df["timestamp"].dt.date <= end_date)
            ]

        if inc_types:
            filtered_df = filtered_df[filtered_df["incident_type"].isin(inc_types)]
        if severities:
            filtered_df = filtered_df[filtered_df["severity_level"].isin(severities)]
        if zones:
            filtered_df = filtered_df[filtered_df["location_zone"].isin(zones)]
        if statuses:
            filtered_df = filtered_df[filtered_df["status"].isin(statuses)]

        return filtered_df, date_range

    def render_kpis(self, df):
        total_incidents = len(df)
        closed_incidents = len(df[df["status"] == "Closed"])
        open_incidents = len(df[df["status"] != "Closed"])

        closed_df = df[(df["status"] == "Closed") & (df["resolution_time_mins"].notna())]
        avg_res_time = closed_df["resolution_time_mins"].mean()
        avg_res_time_str = f"{avg_res_time:.1f} mins" if not pd.isna(avg_res_time) else "N/A"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Incidents", value=total_incidents)
        with col2:
            st.metric(label="Closed Incidents", value=closed_incidents)
        with col3:
            st.metric(label="Active / Open Incidents", value=open_incidents)
        with col4:
            st.metric(label="Avg. Resolution Time", value=avg_res_time_str)

    def render_charts(self, df):
        st.markdown("### Analytics Overview")
        col1, col2 = st.columns(2)

        closed_valid = df[(df["status"] == "Closed") & (df["resolution_time_mins"].notna())]

        with col1:
            if not closed_valid.empty:
                df_sev = (
                    closed_valid.groupby("severity_level")
                    .agg(avg_time=("resolution_time_mins", "mean"), count=("incident_id", "count"))
                    .reset_index()
                )
                df_sev = df_sev.sort_values("severity_level")
                fig_sev = px.bar(
                    df_sev,
                    x="severity_level",
                    y="avg_time",
                    text=df_sev["avg_time"].apply(lambda x: f"{x:.0f}m"),
                    labels={"severity_level": "Severity Level", "avg_time": "Avg Time (mins)"},
                    hover_data=["count"],
                    title="Avg Resolution Time by Severity",
                )
                fig_sev.update_traces(textposition="outside")
                st.plotly_chart(fig_sev, width="stretch")
            else:
                st.info("Not enough data for Avg Resolution Time by Severity")

        with col2:
            if not closed_valid.empty:
                df_type = (
                    closed_valid.groupby("incident_type")
                    .agg(avg_time=("resolution_time_mins", "mean"), count=("incident_id", "count"))
                    .reset_index()
                    .sort_values("avg_time", ascending=False)
                )
                fig_type = px.bar(
                    df_type,
                    x="incident_type",
                    y="avg_time",
                    text=df_type["avg_time"].apply(lambda x: f"{x:.0f}m"),
                    labels={"incident_type": "Incident Type", "avg_time": "Avg Time (mins)"},
                    hover_data=["count"],
                    title="Avg Resolution Time by Incident Type",
                )
                fig_type.update_traces(textposition="outside")
                st.plotly_chart(fig_type, width="stretch")
            else:
                st.info("Not enough data for Avg Resolution Time by Incident Type")

        st.markdown("---")
        col3, col4 = st.columns(2)

        with col3:
            type_counts = df["incident_type"].value_counts().reset_index()
            type_counts.columns = ["incident_type", "count"]
            fig_freq = px.bar(
                type_counts,
                x="incident_type",
                y="count",
                text="count",
                labels={"incident_type": "Incident Type", "count": "Number of Incidents"},
                title="Most Frequent Emergency Types",
            )
            fig_freq.update_traces(textposition="outside")
            st.plotly_chart(fig_freq, width="stretch")

        with col4:
            zone_counts = df.groupby(["location_zone", "status"]).size().reset_index(name="count")
            fig_zone = px.bar(
                zone_counts,
                x="location_zone",
                y="count",
                color="status",
                labels={"location_zone": "Zone", "count": "Incidents Count"},
                title="Incidents per Zone (Grouped by Status)",
                barmode="stack",
            )
            st.plotly_chart(fig_zone, width="stretch")

    def render_hourly_trend(self, df, date_range):
        st.markdown("### Hourly Incident Trend")

        target_date = (
            date_range[0]
            if isinstance(date_range, (list, tuple)) and len(date_range) > 0
            else date.today()
        )
        st.caption(
            f"Showing hourly trends for the selected date: **{target_date}**. "
            "(Hours with 0 incidents are included)."
        )

        day_df = df[df["timestamp"].dt.date == target_date]
        if day_df.empty:
            st.warning(f"No incidents reported on {target_date}.")
            return

        day_df = day_df.copy()
        day_df["hour"] = day_df["timestamp"].dt.hour
        hourly_counts = day_df.groupby("hour").size().reset_index(name="count")

        all_hours = pd.DataFrame({"hour": range(24)})
        hourly_counts = pd.merge(all_hours, hourly_counts, on="hour", how="left").fillna(0)
        hourly_counts["hour_label"] = hourly_counts["hour"].apply(lambda x: f"{x:02d}:00")

        fig_hour = px.line(
            hourly_counts,
            x="hour_label",
            y="count",
            markers=True,
            labels={"hour_label": "Time of Day", "count": "Number of Incidents"},
            title=f"Incident Trend on {target_date}",
        )
        fig_hour.update_yaxes(tick0=0, dtick=1)
        st.plotly_chart(fig_hour, width="stretch")

    def render_map(self, incidents_df, responders_df):
        st.markdown("### Live Resources vs Active Incidents Map")

        zone_coords = {
            "Zone A": [30.0444, 31.2357],
            "Zone B": [30.0550, 31.2450],
            "Zone C": [30.0350, 31.2250],
            "Zone D": [30.0650, 31.2550],
        }

        active_incidents = incidents_df[incidents_df["status"] != "Closed"]
        inc_counts = active_incidents.groupby("location_zone").size().to_dict()

        avail_res = responders_df[responders_df["status"] == "Available"].groupby("current_zone").size().to_dict()
        busy_res = responders_df[responders_df["status"] == "Busy"].groupby("current_zone").size().to_dict()
        off_res = responders_df[responders_df["status"] == "Offline"].groupby("current_zone").size().to_dict()

        m = folium.Map(location=[30.0500, 31.2400], zoom_start=13, tiles="OpenStreetMap")

        for zone, coords in zone_coords.items():
            inc_count = inc_counts.get(zone, 0)
            av_count = avail_res.get(zone, 0)
            bsy_count = busy_res.get(zone, 0)
            off_count = off_res.get(zone, 0)
            ratio = f"{av_count}:{inc_count}" if inc_count > 0 else "N/A"

            if inc_count > 0 and av_count == 0:
                color, icon = "red", "exclamation-circle"
            elif inc_count > av_count:
                color, icon = "orange", "warning"
            else:
                color, icon = "green", "check-circle"

            popup_html = f"""
            <b>{zone}</b><br>
            Active Incidents: {inc_count}<br>
            Available Resources: {av_count}<br>
            Busy Resources: {bsy_count}<br>
            Offline Resources: {off_count}<br>
            <hr>
            <i>Ratio (Avail Res : Active Inc): {ratio}</i>
            """

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{zone} Click for details",
                icon=folium.Icon(color=color, icon=icon, prefix="fa"),
            ).add_to(m)

        st_folium(m, width=1200, height=500)

    def run(self):
        st.title("Emergency Analytics Dashboard")

        incidents, responders = self.load_data()
        if incidents.empty or responders.empty:
            return

        filtered_incidents, date_range = self.apply_filters(incidents)
        self.render_kpis(filtered_incidents)
        st.markdown("---")
        self.render_charts(filtered_incidents)
        st.markdown("---")
        self.render_hourly_trend(filtered_incidents, date_range)
        st.markdown("---")
        self.render_map(filtered_incidents, responders)


EmergencyDashboard().run()
