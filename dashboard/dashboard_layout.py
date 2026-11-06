import pandas as pd
from dash import dcc, html

from dashboard.colours import SHELL_VERY_DARK_GREY, SHELL_WHITE
from dashboard.layout_components import create_dashboard_panel


def create_layout(
    ipp_data: pd.DataFrame,
    op_data: pd.DataFrame = None,
    ipp_weekly_data: pd.DataFrame = None,
):
    if op_data is None:
        op_data = ipp_data
    if ipp_weekly_data is None:
        ipp_weekly_data = ipp_data
    return html.Div(
        style={
            "fontFamily": "Segoe UI, Arial, sans-serif",
            "margin": "24px",
            "backgroundColor": SHELL_WHITE,
            "color": SHELL_VERY_DARK_GREY,
        },
        children=[
            dcc.Tabs(
                id="dashboard-tabs",
                value="ipp-lookback",
                children=[
                    dcc.Tab(
                        label="IPP Lookback",
                        value="ipp-lookback",
                        children=create_dashboard_panel(
                            ipp_data, "IPP Lookback", "ipp", "month",
                            include_well_status=False,
                        ),
                    ),
                    dcc.Tab(
                        label="IPP Weekly",
                        value="ipp-weekly",
                        children=create_dashboard_panel(
                            ipp_weekly_data, "IPP Weekly", "ipp_week",
                            "week", include_well_status=False,
                        ),
                    ),
                    dcc.Tab(
                        label="OP Lookback",
                        value="op-lookback",
                        children=create_dashboard_panel(
                            op_data, "OP Lookback", "op", "year"
                        ),
                    ),
                ],
            )
        ],
    )
