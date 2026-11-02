# City Service Requests Dashboard

An interactive Streamlit dashboard exploring resolution speed, request demand, and resident satisfaction in a synthetic City 311 service-request dataset.

## Published links

- Streamlit app: **Add the deployed Streamlit Community Cloud URL here**
- Public GitHub repository: **Add the public repository URL here**

## Project and audience

The dashboard is intended for city operations teams and residents who want to explore how service requests are handled. It summarizes patterns in the supplied teaching dataset and is not an official report about any real city.

## Analysis questions

1. Which request categories take the longest to resolve, and how does resolution time vary by priority?
2. How does request volume change over time, and do categories show different monthly patterns?
3. Do slower resolutions tend to have lower resident satisfaction, and does that relationship differ by channel?

The dashboard provides four filter-responsive summary metrics: unique requests, median resolution time, the share of requests past their SLA, and average satisfaction. Date, category, district, channel, and priority filters update the metrics, three analysis charts, and a district activity schematic. The schematic is illustrative only because the source data does not contain district coordinates.

## Dataset and source

`dashboard_data.csv` is the reduced dashboard dataset supplied with the Deliverable 2 teaching example. Its source is an instructor-provided synthetic City 311 dataset, not a live municipal data feed. The synthetic rows were created for coursework and should not be interpreted as actual service performance. Only the reduced CSV needed by the app is included in the deployment package; the larger raw data file is not required to run the dashboard.

## Run locally

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Keep `app.py`, `dashboard_data.csv`, and `requirements.txt` in the same repository root. Streamlit Community Cloud can deploy the app by selecting this repository and setting the main file to `app.py`.

## AI-use statement

Generative AI assisted with dashboard implementation, chart setup, and documentation. The student is responsible for reviewing the code, validating the filters and results, and presenting the analysis accurately.