import pandas as pd
from dash import dcc, html

from dashboard.chart import make_chart
from dashboard.colours import SHELL_VERY_DARK_GREY, SHELL_YELLOW
from dashboard.data_processing import (
    filter_data,
    get_default_filter_values,
    get_filter_options,
    get_metric_options,
)


def create_dropdown(label, dropdown_id, options, width, multi=True, value=None):
    placeholder = {
        "Facility": "All facilities",
        "Well": "All wells",
        "Well Status": "All well statuses",
    }.get(label, f"All {label.lower()}s")
    return html.Div([
        html.Label(label),
        dcc.Dropdown(
            id=dropdown_id,
            options=options,
            value=[] if value is None and multi else value,
            multi=multi,
            clearable=True,
            placeholder=placeholder,
        ),
    ], style={"width": width})


def create_dashboard_panel(
    data: pd.DataFrame,
    title: str,
    id_prefix: str,
    period: str,
    include_well_status: bool = True,
):
    filter_options = get_filter_options(data)
    default_filters = get_default_filter_values(data)
    metric_options = get_metric_options(data)
    default_metric = "SUBSURFACE" if any(
        option["value"] == "SUBSURFACE" for option in metric_options
    ) else ("AFS" if metric_options else None)
    default_view_data = filter_data(
        data,
        facility=default_filters["facility"],
        well_status=default_filters["well_status"] if include_well_status else None,
    )

    sidebar = html.Aside(
        style={
            "width": "220px",
            "minWidth": "220px",
            "padding": "18px",
            "boxSizing": "border-box",
            "borderRight": f"1px solid {SHELL_VERY_DARK_GREY}33",
            "backgroundColor": "#F7F7F7",
            "position": "sticky",
            "top": "24px",
            "alignSelf": "flex-start",
            "minHeight": "520px",
            "borderRadius": "6px",
        },
        children=[
            html.H2("Filters", style={"margin": "0 0 16px 0"}),
            html.Div([
                html.Label("Metric"),
                dcc.Dropdown(
                    id=f"{id_prefix}-metric",
                    options=metric_options,
                    value=default_metric,
                    clearable=False,
                ),
            ], style={"marginBottom": "14px"}),
            html.Div(
                style={"display": "flex", "flexDirection": "column", "gap": "14px"},
                children=[
                    create_dropdown(
                        "Facility", f"{id_prefix}-facility",
                        filter_options["facility"], "100%",
                        value=default_filters["facility"],
                    ),
                    create_dropdown(
                        "Well", f"{id_prefix}-well",
                        filter_options["well"], "100%",
                    ),
                    *([
                        create_dropdown(
                            "Well Status", f"{id_prefix}-well_status",
                            filter_options["well_status"], "100%",
                            value=default_filters["well_status"],
                        ),
                    ] if include_well_status else []),
                ],
            ),
            html.Button(
                "Refresh from Databricks",
                id=f"{id_prefix}-refresh",
                n_clicks=0,
                style={
                    "width": "100%",
                    "height": "38px",
                    "marginTop": "18px",
                    "backgroundColor": SHELL_YELLOW,
                    "borderRadius": "4px",
                    "cursor": "pointer",
                },
            ),
        ],
    )
    main = html.Main(
        style={"flex": "1", "minWidth": "0", "padding": "0 0 0 20px"},
        children=[
            html.H1(title),
            html.Div("Databricks SQL Warehouse dashboard"),
            html.Div(id=f"{id_prefix}-status", style={"minHeight": "24px"}),
            dcc.Loading(
                html.Iframe(
                    id=f"{id_prefix}-chart",
                    srcDoc=make_chart(
                        default_view_data,
                        default_metric,
                        period,
                        use_well_status=include_well_status,
                    ) if default_metric else {},
                    style={
                        "width": "100%", "height": "760px",
                        "border": "none", "display": "block",
                    },
                ),
            ),
        ],
    )
    return html.Div(
        style={"display": "flex", "alignItems": "stretch", "gap": "0"},
        children=[sidebar, main],
    )
