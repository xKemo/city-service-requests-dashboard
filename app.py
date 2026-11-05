import json
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Florida Crime Patterns | 2025",
    page_icon=":material/map:",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("dashboard_data.csv")
GEOJSON_FILE = Path(__file__).with_name("florida_counties.geojson")
HEAT_COLORS = ["#713A8E", "#2864C5", "#24A66A", "#F2D13D", "#D84343"]


@st.cache_data
def load_dashboard_data() -> tuple[pd.DataFrame, dict]:
    data = pd.read_csv(DATA_FILE, dtype={"county_fips": str})
    data["month"] = pd.to_datetime(data["month"], format="%Y-%m", errors="coerce")
    data["incidents"] = pd.to_numeric(data["incidents"], errors="coerce").fillna(0)
    with GEOJSON_FILE.open(encoding="utf-8") as geojson_file:
        county_geojson = json.load(geojson_file)
    return data.dropna(subset=["month"]), county_geojson


try:
    crime_data, florida_geojson = load_dashboard_data()
except FileNotFoundError as error:
    st.error(f"Required dashboard file is missing: {error.filename}")
    st.stop()

if crime_data.empty:
    st.error("The Florida crime dataset contains no usable records.")
    st.stop()

st.title("Florida Crime Patterns | 2025")
st.write(
    "Explore where reported incidents were concentrated, how counts changed by month, "
    "and which offense types appeared most often."
)
st.caption(
    "Intended audience: Florida residents, students, and public-safety analysts. "
    "Counts describe FBI NIBRS reports, not every crime that occurred."
)

with st.sidebar:
    st.header("Explore the data")
    available_months = sorted(crime_data["month"].unique())
    month_range = st.select_slider(
        "Month range",
        options=available_months,
        value=(available_months[0], available_months[-1]),
        format_func=lambda month: month.strftime("%b %Y"),
    )
    county_options = sorted(crime_data["county"].unique())
    selected_counties = st.multiselect(
        "County",
        county_options,
        default=county_options,
    )
    offense_options = sorted(crime_data["offense_name"].unique())
    selected_offenses = st.multiselect(
        "Primary offense",
        offense_options,
        default=offense_options,
    )
    location_options = sorted(crime_data["location_name"].unique())
    selected_locations = st.multiselect(
        "Location type",
        location_options,
        default=location_options,
    )

filtered = crime_data.loc[
    crime_data["month"].between(month_range[0], month_range[1])
    & crime_data["county"].isin(selected_counties)
    & crime_data["offense_name"].isin(selected_offenses)
    & crime_data["location_name"].isin(selected_locations)
].copy()

if filtered.empty:
    st.info("No reported incidents match these filters. Expand your selections to see results.")
    st.stop()

county_counts = filtered.groupby("county_fips", as_index=False)["incidents"].sum()
county_names = (
    crime_data[["county_fips", "county"]]
    .drop_duplicates("county_fips")
    .set_index("county_fips")["county"]
)
county_counts["county"] = county_counts["county_fips"].map(county_names)
top_county = county_counts.loc[county_counts["incidents"].idxmax()]
offense_counts = filtered.groupby("offense_name")["incidents"].sum().sort_values(ascending=False)
top_offense = offense_counts.index[0]
total_incidents = int(filtered["incidents"].sum())

st.subheader("At a glance")
metric_columns = st.columns(4)
metric_columns[0].metric("Reported incidents", f"{total_incidents:,}")
metric_columns[1].metric("Counties represented", f"{len(county_counts):,}")
metric_columns[2].metric("Highest-count county", str(top_county["county"]))
metric_columns[3].metric("Most common primary offense", top_offense)

st.divider()
st.subheader("Where reported incidents were concentrated")
st.write(
    "County color shows the count of mapped incidents in the current selection. "
    "The color scale uses a log transform so both high- and lower-count counties remain visible."
)

geo_counties = pd.DataFrame(
    [
        {
            "county_fips": feature["properties"]["GEO_ID"][-5:],
            "county": feature["properties"]["NAME"],
        }
        for feature in florida_geojson["features"]
    ]
)
reporting_fips = set(crime_data["county_fips"].unique())
county_map = geo_counties.merge(
    county_counts[["county_fips", "incidents"]],
    on="county_fips",
    how="left",
)
county_map["geo_id"] = "0500000US" + county_map["county_fips"]
county_map["is_selected"] = county_map["county_fips"].isin(filtered["county_fips"].unique())
county_map["has_source_reports"] = county_map["county_fips"].isin(reporting_fips)
county_map["color_value"] = county_map["incidents"].map(
    lambda count: math.log10(count + 1) if pd.notna(count) else None
)
county_map.loc[~county_map["is_selected"] | ~county_map["has_source_reports"], "color_value"] = None
county_map["incidents"] = county_map["incidents"].fillna(0).astype(int)
max_log_count = max(
    1.0,
    math.log10(max(1, int(county_map["incidents"].max())) + 1),
)
tick_values = [value for value in range(math.ceil(max_log_count) + 1) if value <= max_log_count]
tick_labels = ["0" if value == 0 else f"{10**value:,}" for value in tick_values]

heat_map = px.choropleth(
    county_map,
    geojson=florida_geojson,
    locations="geo_id",
    featureidkey="properties.GEO_ID",
    color="color_value",
    hover_name="county",
    hover_data={
        "county_fips": False,
        "geo_id": False,
        "color_value": False,
        "incidents": ":,d",
        "is_selected": False,
        "has_source_reports": False,
    },
    color_continuous_scale=HEAT_COLORS,
    range_color=(0, max_log_count),
    labels={"color_value": "Reported incidents (log scale)", "incidents": "Incidents"},
)
heat_map.update_traces(marker_line_color="#FFFFFF", marker_line_width=0.8)
heat_map.update_coloraxes(
    colorbar=dict(
        title=dict(text="Reported incidents", font=dict(color="#F3F4F6")),
        tickvals=tick_values,
        ticktext=tick_labels,
        tickfont=dict(color="#F3F4F6"),
        outlinecolor="#64748B",
    )
)
heat_map.update_geos(
    fitbounds="locations",
    visible=False,
    showland=True,
    landcolor="#263238",
    bgcolor="#111827",
)
heat_map.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font_color="#F3F4F6",
    margin=dict(l=0, r=0, t=10, b=0),
    height=610,
)
st.plotly_chart(heat_map, width="stretch")
st.caption(
    f"Highest count in the current selection: {top_county['county']} "
    f"({int(top_county['incidents']):,} incidents). Gray counties have no incidents "
    "matching the current filters or no mapped county reports in this extract; they "
    "should not be read as zero crime."
)

st.divider()
st.subheader("Reported incidents by month")
monthly = (
    filtered.groupby("month", as_index=False)["incidents"]
    .sum()
    .sort_values("month")
)
month_chart = px.line(
    monthly,
    x="month",
    y="incidents",
    markers=True,
    labels={"month": "Month", "incidents": "Reported incidents"},
    color_discrete_sequence=["#2864C5"],
)
month_chart.update_layout(
    template="plotly_white",
    margin=dict(l=10, r=10, t=15, b=10),
    height=360,
)
st.plotly_chart(month_chart, width="stretch")

st.divider()
st.subheader("Most common primary offense types")
top_offenses = (
    filtered.groupby("offense_name", as_index=False)["incidents"]
    .sum()
    .nlargest(12, "incidents")
    .sort_values("incidents")
)
offense_chart = px.bar(
    top_offenses,
    x="incidents",
    y="offense_name",
    orientation="h",
    labels={"incidents": "Incidents", "offense_name": "Primary offense type"},
    color="incidents",
    color_continuous_scale=HEAT_COLORS,
)
offense_chart.update_layout(
    template="plotly_white",
    showlegend=False,
    coloraxis_showscale=False,
    margin=dict(l=10, r=10, t=15, b=10),
    height=470,
)
st.plotly_chart(offense_chart, width="stretch")

st.divider()
st.caption(
    "Source: FBI Crime Data Explorer, Florida NIBRS 2025 extract. The dashboard assigns "
    "each incident its first listed offense and location to avoid counting the same incident "
    "multiple times. County is based on the reporting agency, not an incident address. "
    "Records without an unambiguous Florida county are excluded. Counts are not adjusted "
    "for population and do not measure all crime."
)