from dash import Dash

from dashboard.callbacks import register_callbacks
from dashboard.data_processing import load_all_data
from dashboard.layout import create_layout


print("Connecting to Databricks and loading data...")
ipp_combined_data, op_combined_data = load_all_data()
print(
    f"Loaded {len(ipp_combined_data):,} IPP records and "
    f"{len(op_combined_data):,} OP records"
)

app = Dash(__name__, title="IPP LookBack Dashboard")
server = app.server
app.layout = create_layout(ipp_combined_data, op_combined_data)

register_callbacks(
    app,
    {"combined_data": ipp_combined_data},
    id_prefix="ipp",
    period="month",
    include_well_status=False,
    forecast_key="IPP_Forecasts",
)
register_callbacks(
    app,
    {"combined_data": op_combined_data},
    id_prefix="op",
    period="year",
    forecast_key="OP_Forecasts",
)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port="8050")
