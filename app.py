from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="City Service Requests",
    page_icon=":material/bar_chart:",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("dashboard_data.csv")
CHART_COLORS = ["#126B5B", "#E29A35", "#D85D4A", "#5276A7", "#8B6F9D", "#7A8F46"]


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_FILE)
    data["created_date"] = pd.to_datetime(data["created_date"], errors="coerce")
    for column in ("resolution_days", "satisfaction_score", "is_late"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["created_date"]).copy()
    data["month_start"] = data["created_date"].dt.to_period("M").dt.to_timestamp()
    return data


def format_count(value: int) -> str:
    return f"{value:,.0f}"


st.title("City Service Requests")
st.write(
    "Explore how quickly requests are resolved, when demand changes, and how "
    "resolution time relates to resident satisfaction."
)
st.caption(
    "Intended audience: city operations teams and residents interested in "
    "service delivery. This dashboard uses synthetic teaching data."
)

try:
    requests = load_data()
except FileNotFoundError:
    st.error("dashboard_data.csv was not found beside app.py.")
    st.stop()

if requests.empty:
    st.error("The dataset has no rows with a valid created date.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    date_min = requests["created_date"].min().date()
    date_max = requests["created_date"].max().date()
    date_selection = st.date_input(
        "Created date",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    def multiselect_filter(label: str, column: str) -> list[str]:
        options = sorted(requests[column].dropna().astype(str).unique().tolist())
        return st.multiselect(label, options, default=options)

    selected_categories = multiselect_filter("Category", "category")
    selected_districts = multiselect_filter("District", "district")
    selected_channels = multiselect_filter("Channel", "channel")
    selected_priorities = multiselect_filter("Priority", "priority")

if isinstance(date_selection, tuple) and len(date_selection) == 2:
    start_date, end_date = date_selection
else:
    start_date = end_date = date_selection

filtered = requests.loc[
    requests["created_date"].dt.date.between(start_date, end_date)
    & requests["category"].astype(str).isin(selected_categories)
    & requests["district"].astype(str).isin(selected_districts)
    & requests["channel"].astype(str).isin(selected_channels)
    & requests["priority"].astype(str).isin(selected_priorities)
].copy()

st.subheader("At a glance")
if filtered.empty:
    st.info("No requests match the selected filters. Adjust the filters to see results.")
    st.stop()

closed_requests = filtered.loc[filtered["resolution_days"].notna()]
late_values = filtered["is_late"].dropna()
satisfaction_values = filtered["satisfaction_score"].dropna()

metric_columns = st.columns(4)
metric_columns[0].metric("Requests", format_count(filtered["request_id"].nunique()))
metric_columns[1].metric(
    "Median resolution",
    f"{closed_requests['resolution_days'].median():.1f} days"
    if not closed_requests.empty
    else "N/A",
)
metric_columns[2].metric(
    "Past SLA",
    f"{late_values.mean() * 100:.1f}%" if not late_values.empty else "N/A",
    help="Share of requests with a recorded SLA result that were late.",
)
metric_columns[3].metric(
    "Average satisfaction",
    f"{satisfaction_values.mean():.2f} / 5" if not satisfaction_values.empty else "N/A",
)

st.divider()
st.subheader("Resolution speed")
st.write(
    "Which categories take longest to resolve, and how does the pattern vary by priority?"
)
speed_data = closed_requests.groupby(
    ["category", "priority"], as_index=False, observed=True
)["resolution_days"].median()
category_order = (
    closed_requests.groupby("category")["resolution_days"]
    .median()
    .sort_values()
    .index.tolist()
)
speed_chart = px.bar(
    speed_data,
    x="resolution_days",
    y="category",
    color="priority",
    barmode="group",
    category_orders={"category": category_order},
    color_discrete_sequence=CHART_COLORS,
    labels={
        "resolution_days": "Median resolution time (days)",
        "category": "Request category",
        "priority": "Priority",
    },
)
speed_chart.update_layout(
    template="plotly_white",
    legend_title_text="Priority",
    margin=dict(l=10, r=10, t=15, b=10),
    height=420,
)
st.plotly_chart(speed_chart, width="stretch")
if not speed_data.empty:
    slowest = speed_data.groupby("category")["resolution_days"].median().idxmax()
    slowest_days = speed_data.groupby("category")["resolution_days"].median().max()
    st.caption(
        f"Among the filtered closed requests, {slowest} has the highest category-level "
        f"median resolution time ({slowest_days:.1f} days)."
    )
else:
    st.caption("No closed requests with resolution times match these filters.")

st.divider()
st.subheader("Request demand over time")
st.write("How has monthly request volume changed, and do categories follow different patterns?")
demand_data = (
    filtered.groupby(["month_start", "category"], as_index=False, observed=True)["request_id"]
    .nunique()
    .rename(columns={"request_id": "requests"})
)
demand_chart = px.line(
    demand_data,
    x="month_start",
    y="requests",
    color="category",
    markers=True,
    color_discrete_sequence=CHART_COLORS,
    labels={
        "month_start": "Month",
        "requests": "Unique requests",
        "category": "Category",
    },
)
demand_chart.update_layout(
    template="plotly_white",
    legend_title_text="Category",
    margin=dict(l=10, r=10, t=15, b=10),
    height=410,
)
st.plotly_chart(demand_chart, width="stretch")
peak_month = demand_data.groupby("month_start")["requests"].sum().idxmax()
peak_total = demand_data.groupby("month_start")["requests"].sum().max()
st.caption(f"Peak month in the current selection: {peak_month:%B %Y} ({peak_total:,.0f} requests).")

st.divider()
st.subheader("District service map")
st.write("A compact view of request volume across the selected districts.")
district_positions = {
    "North End": (1, 2),
    "Downtown": (1, 1),
    "East Side": (2, 1),
    "West End": (0, 1),
    "University": (2, 2),
    "South Park": (1, 0),
}
district_map_data = (
    filtered.loc[filtered["district"].isin(district_positions)]
    .groupby("district", as_index=False, observed=True)
    .agg(requests=("request_id", "nunique"))
)
district_map_data["x"] = district_map_data["district"].map(
    lambda district: district_positions[district][0]
)
district_map_data["y"] = district_map_data["district"].map(
    lambda district: district_positions[district][1]
)
map_column, map_note_column = st.columns([2, 1])
with map_column:
    if district_map_data.empty:
        st.info("No named districts match the current filters.")
    else:
        district_chart = px.scatter(
            district_map_data,
            x="x",
            y="y",
            size="requests",
            color="requests",
            text="district",
            size_max=58,
            color_continuous_scale=["#B8D7CF", "#126B5B"],
            hover_data={"x": False, "y": False, "district": True, "requests": ":,d"},
            labels={"requests": "Unique requests"},
        )
        district_chart.update_traces(
            textposition="middle center",
            textfont=dict(color="#10231F", size=11),
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )
        district_chart.update_layout(
            template="plotly_white",
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=330,
            xaxis=dict(visible=False, range=[-0.65, 2.65], fixedrange=True),
            yaxis=dict(visible=False, range=[-0.55, 2.55], fixedrange=True),
        )
        st.plotly_chart(district_chart, width="stretch")
with map_note_column:
    st.markdown("**Marker size**\n\nUnique requests")
    st.markdown(
        "**Schematic only**\n\n"
        "The dataset contains district names, not geographic coordinates. "
        "Marker positions are illustrative and do not represent actual locations. "
        "Unknown districts are omitted."
    )

st.subheader("Resolution time and resident experience")
st.write(
    "Do requests that take longer to resolve tend to receive lower satisfaction scores, "
    "and does the pattern differ by channel?"
)
experience_data = filtered.dropna(subset=["resolution_days", "satisfaction_score"])
experience_chart = px.scatter(
    experience_data,
    x="resolution_days",
    y="satisfaction_score",
    color="channel",
    hover_data=["category", "district", "priority"],
    opacity=0.62,
    color_discrete_sequence=CHART_COLORS,
    labels={
        "resolution_days": "Resolution time (days)",
        "satisfaction_score": "Satisfaction score (1-5)",
        "channel": "Request channel",
    },
)
experience_chart.update_layout(
    template="plotly_white",
    legend_title_text="Channel",
    margin=dict(l=10, r=10, t=15, b=10),
    height=430,
)
experience_chart.update_yaxes(range=[0.5, 5.5], dtick=1)
st.plotly_chart(experience_chart, width="stretch")
if len(experience_data) > 1:
    correlation = experience_data["resolution_days"].corr(
        experience_data["satisfaction_score"]
    )
    st.caption(
        f"Filtered records show a correlation of {correlation:.2f} between resolution "
        "time and satisfaction. This is descriptive and does not establish causation."
    )
else:
    st.caption("At least two requests with both measures are needed to compare the relationship.")

st.divider()
st.caption(
    "Source: instructor-provided synthetic City 311 teaching dataset. "
    "Counts and averages describe this dataset only; they are not real-world city statistics."
)