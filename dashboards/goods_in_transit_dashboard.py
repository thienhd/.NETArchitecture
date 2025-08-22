import pandas as pd
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Sample data for demonstration purposes
DATA = [
    {
        "PO Number": "PO001",
        "Vendor Name": "Vendor A",
        "Item": "Lens",
        "Quantity PO": 100,
        "Quantity Confirmed": 95,
        "Ex-Factory Date": "2025-01-02",
        "Port Departure Date": "2025-01-05",
        "Port Arrival Date": "2025-01-12",
        "ETA to Hoya Warehouse": "2025-01-18",
        "Actual Arrival Date": "2025-01-19",
        "Shipment Value": 15000,
        "Route": "CN-HN",
    },
    {
        "PO Number": "PO002",
        "Vendor Name": "Vendor B",
        "Item": "Frame",
        "Quantity PO": 200,
        "Quantity Confirmed": 200,
        "Ex-Factory Date": "2025-01-10",
        "Port Departure Date": "2025-01-13",
        "Port Arrival Date": "2025-01-20",
        "ETA to Hoya Warehouse": "2025-01-27",
        "Actual Arrival Date": "2025-01-30",
        "Shipment Value": 30000,
        "Route": "KR-HCM",
    },
    {
        "PO Number": "PO003",
        "Vendor Name": "Vendor C",
        "Item": "Lens",
        "Quantity PO": 150,
        "Quantity Confirmed": 140,
        "Ex-Factory Date": "2025-02-01",
        "Port Departure Date": "2025-02-04",
        "Port Arrival Date": "2025-02-12",
        "ETA to Hoya Warehouse": "2025-02-18",
        "Actual Arrival Date": None,
        "Shipment Value": 22000,
        "Route": "JP-HN",
    },
    {
        "PO Number": "PO004",
        "Vendor Name": "Vendor A",
        "Item": "Lens",
        "Quantity PO": 120,
        "Quantity Confirmed": 110,
        "Ex-Factory Date": "2025-01-15",
        "Port Departure Date": "2025-01-18",
        "Port Arrival Date": "2025-01-25",
        "ETA to Hoya Warehouse": "2025-02-02",
        "Actual Arrival Date": "2025-02-10",
        "Shipment Value": 18000,
        "Route": "CN-HCM",
    },
    {
        "PO Number": "PO005",
        "Vendor Name": "Vendor B",
        "Item": "Frame",
        "Quantity PO": 80,
        "Quantity Confirmed": 70,
        "Ex-Factory Date": "2025-02-05",
        "Port Departure Date": None,
        "Port Arrival Date": None,
        "ETA to Hoya Warehouse": "2025-02-20",
        "Actual Arrival Date": None,
        "Shipment Value": 12000,
        "Route": "KR-HN",
    },
]

# Convert to DataFrame and parse dates
_df = pd.DataFrame(DATA)
for col in [
    "Ex-Factory Date",
    "Port Departure Date",
    "Port Arrival Date",
    "ETA to Hoya Warehouse",
    "Actual Arrival Date",
]:
    _df[col] = pd.to_datetime(_df[col])

# Helper calculations
_df["Delay Days"] = (_df["Actual Arrival Date"] - _df["ETA to Hoya Warehouse"]).dt.days
_df["Is Delayed"] = _df["Delay Days"] > 0

# KPI 1: Confirmed POs
confirmed_pos = _df[~_df["Quantity Confirmed"].isna()]
po_confirmed_count = confirmed_pos["PO Number"].nunique()
qty_confirmed_total = confirmed_pos["Quantity Confirmed"].sum()
value_confirmed_total = confirmed_pos["Shipment Value"].sum()

# KPI 2: Goods in transit (GIT)
current_date = pd.Timestamp.now()
_git = _df[_df["Actual Arrival Date"].isna()]
po_git_count = _git["PO Number"].nunique()
qty_git_total = _git["Quantity Confirmed"].sum()
value_git_total = _git["Shipment Value"].sum()
shipment_delay_pct = (
    _git[_git["ETA to Hoya Warehouse"] < current_date].shape[0] / max(po_git_count, 1)
    if po_git_count
    else 0
)

# KPI 3: ETA accuracy
_eta_diff = (_df["Actual Arrival Date"] - _df["ETA to Hoya Warehouse"]).abs().dt.days
eta_accuracy_system = 100 - _eta_diff.mean() * 100.0 / 7  # using 7-day tolerance
eta_accuracy_by_vendor = (
    _df.groupby("Vendor Name")[["Actual Arrival Date", "ETA to Hoya Warehouse"]]
    .apply(lambda x: 100 - (x["Actual Arrival Date"] - x["ETA to Hoya Warehouse"]).abs().dt.days.mean() * 100.0 / 7)
    .reset_index(name="ETA Accuracy (%)")
)

# Timeline chart
_timeline_df = _df.melt(
    id_vars=["PO Number"],
    value_vars=[
        "Ex-Factory Date",
        "Port Departure Date",
        "Port Arrival Date",
        "ETA to Hoya Warehouse",
        "Actual Arrival Date",
    ],
    var_name="Stage",
    value_name="Date",
)
fig_timeline = px.line(_timeline_df, x="Date", y="Stage", color="PO Number", markers=True)

# Heatmap: delay rate by vendor and route
heatmap_df = (
    _df.groupby(["Vendor Name", "Route"])["Is Delayed"].mean().reset_index()
)
fig_heatmap = px.density_heatmap(
    heatmap_df,
    x="Route",
    y="Vendor Name",
    z="Is Delayed",
    nbinsx=len(heatmap_df["Route"].unique()),
    nbinsy=len(heatmap_df["Vendor Name"].unique()),
    color_continuous_scale="Reds",
    labels={"Is Delayed": "Delay Rate"},
)

# Ranking chart: top 5 vendors by delay rate
ranking_df = (
    _df.groupby("Vendor Name")["Is Delayed"].mean().sort_values(ascending=False).reset_index()
)
fig_ranking = px.bar(ranking_df.head(5), x="Vendor Name", y="Is Delayed", labels={"Is Delayed": "Delay Rate"})

# Line chart: ETA vs Actual Arrival (accuracy over time)
line_df = _df.dropna(subset=["Actual Arrival Date"]).copy()
line_df["ETA"] = line_df["ETA to Hoya Warehouse"]
line_df["Actual"] = line_df["Actual Arrival Date"]
fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=line_df["PO Number"], y=line_df["ETA"], mode="lines+markers", name="ETA"))
fig_line.add_trace(go.Scatter(x=line_df["PO Number"], y=line_df["Actual"], mode="lines+markers", name="Actual"))
fig_line.update_layout(xaxis_title="PO Number", yaxis_title="Date")

# Table of abnormal POs
abnormal_mask = (
    (_df["Is Delayed"] & (_df["Delay Days"] > 7))
    | (_df["Quantity Confirmed"] < _df["Quantity PO"])
    | _df[["Port Departure Date", "Port Arrival Date"]].isna().any(axis=1)
)
abnormal_df = _df[abnormal_mask][
    [
        "PO Number",
        "Vendor Name",
        "Quantity PO",
        "Quantity Confirmed",
        "ETA to Hoya Warehouse",
        "Actual Arrival Date",
        "Delay Days",
    ]
]

# Dashboard layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container(
    [
        html.H1("Goods in Transit Dashboard"),
        dbc.Row(
            [
                dbc.Col(dbc.Card([dbc.CardHeader("PO Confirmed"), dbc.CardBody(html.H4(f"{po_confirmed_count}"))])),
                dbc.Col(dbc.Card([dbc.CardHeader("Qty Confirmed"), dbc.CardBody(html.H4(f"{qty_confirmed_total}"))])),
                dbc.Col(dbc.Card([dbc.CardHeader("Value Confirmed"), dbc.CardBody(html.H4(f"{value_confirmed_total:,.0f}"))])),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card([dbc.CardHeader("PO in GIT"), dbc.CardBody(html.H4(f"{po_git_count}"))])),
                dbc.Col(dbc.Card([dbc.CardHeader("Qty in GIT"), dbc.CardBody(html.H4(f"{qty_git_total}"))])),
                dbc.Col(dbc.Card([dbc.CardHeader("Value in GIT"), dbc.CardBody(html.H4(f"{value_git_total:,.0f}"))])),
                dbc.Col(dbc.Card([dbc.CardHeader("% Shipment Delayed"), dbc.CardBody(html.H4(f"{shipment_delay_pct:.0%}"))])),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card([dbc.CardHeader("ETA Accuracy (System)"), dbc.CardBody(html.H4(f"{eta_accuracy_system:.1f}%"))])),
            ],
            className="mb-4",
        ),
        dcc.Graph(figure=fig_timeline, id="timeline"),
        dcc.Graph(figure=fig_heatmap, id="heatmap"),
        dcc.Graph(figure=fig_ranking, id="ranking"),
        dcc.Graph(figure=fig_line, id="eta_vs_actual"),
        dash_table.DataTable(
            abnormal_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in abnormal_df.columns],
            page_size=10,
            style_table={"overflowX": "auto"},
        ),
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True)
