# Florida Crime Patterns Dashboard

An interactive Streamlit dashboard exploring FBI NIBRS-reported crime incidents in Florida during 2025, including county-level concentration, monthly counts, and offense types.

## Published links

- Streamlit app: https://xkemo-city-service-requests-dashboard-app-c3thhi.streamlit.app/
- Public GitHub repository: https://github.com/xKemo/city-service-requests-dashboard

## Project and audience

The dashboard is intended for Florida residents, students, and public-safety analysts who want to explore reported incident patterns. Date, county, primary offense, and location-type filters update the metrics and all visualizations.

## Analysis questions

1. Which Florida counties have the highest counts of reported incidents in this extract?
2. How do reported incident counts change month to month?
3. Which primary offense types appear most often?

The dashboard includes four summary metrics and three visualizations: a county choropleth heat map, a monthly incident trend, and a ranking of primary offense types. Heat colors progress from purple and blue through green and yellow to red as reported counts rise. The map uses a logarithmic color scale to keep lower-count counties visible.

## Dataset and limitations

`dashboard_data.csv` is a reduced dataset prepared from the FBI Crime Data Explorer Florida 2025 NIBRS extract (`FL-2025.zip`). The map boundary file, `florida_counties.geojson`, contains Florida county outlines derived from the Plotly county GeoJSON dataset, which is based on U.S. Census county identifiers.

Each incident is assigned its first listed offense and location so it contributes once to incident counts. County reflects the reporting agency’s county, not a verified incident address. Records without an unambiguous Florida county are excluded; only 54 counties have mapped reports in this extract. Counties without mapped records appear gray and must not be interpreted as having zero crime. Counts are not adjusted for population, reporting coverage varies, and the FBI data represents reported incidents rather than all crimes that occurred.

## Run locally

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Keep `app.py`, `dashboard_data.csv`, `florida_counties.geojson`, and `requirements.txt` together in the repository root.

## AI-use statement

Generative AI assisted with dashboard implementation, map configuration, and documentation.
