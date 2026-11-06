from dash import Input, Output, callback_context

from dashboard.chart import make_chart
from dashboard.data_processing import (
    filter_data,
    get_filter_options,
    load_data,
    prepare_data,
)


def register_callbacks(
    app,
    data_state: dict,
    id_prefix: str = "op",
    period: str = "year",
    include_well_status: bool = True,
    forecast_key: str = "OP_Forecasts",
):
    outputs = [
        Output(f"{id_prefix}-chart", "srcDoc"),
        Output(f"{id_prefix}-status", "children"),
        Output(f"{id_prefix}-facility", "options"),
        Output(f"{id_prefix}-well", "options"),
    ]
    inputs = [
        Input(f"{id_prefix}-metric", "value"),
        Input(f"{id_prefix}-facility", "value"),
        Input(f"{id_prefix}-well", "value"),
    ]
    if include_well_status:
        outputs.append(Output(f"{id_prefix}-well_status", "options"))
        inputs = [
            Input(f"{id_prefix}-metric", "value"),
            Input(f"{id_prefix}-facility", "value"),
            Input(f"{id_prefix}-well", "value"),
            Input(f"{id_prefix}-well_status", "value"),
        ]
    inputs.append(Input(f"{id_prefix}-refresh", "n_clicks"))

    @app.callback(
        *outputs,
        *inputs,
    )
    def update_dashboard(*values):
        if include_well_status:
            metric, facility, well, well_status = values[:4]
            remaining = values[4:]
        else:
            metric, facility, well = values[:3]
            well_status = None
            remaining = values[3:]

        refresh_clicks = remaining[0]
        refresh_triggered = (
            callback_context.triggered
            and callback_context.triggered[0]["prop_id"] == f"{id_prefix}-refresh.n_clicks"
            and refresh_clicks > 0
        )

        if refresh_triggered:
            actuals, forecasts = load_data(forecast_key)
            data_state["combined_data"] = prepare_data(actuals, forecasts)
            if period == "month":
                data_state["combined_data"] = data_state["combined_data"][
                    data_state["combined_data"]["Date"] >= "2025-01-01"
                ]
                data_state["combined_data"] = data_state["combined_data"].drop(
                    columns=["WellStatus"], errors="ignore"
                )
            elif period == "week":
                data_state["combined_data"] = data_state["combined_data"][
                    data_state["combined_data"]["Date"] >= "2026-01-01"
                ]
                data_state["combined_data"] = data_state["combined_data"].drop(
                    columns=["WellStatus"], errors="ignore"
                )
            status = (
                f"Refreshed {len(data_state['combined_data']):,} records from Databricks"
            )
        else:
            status = f"Showing {len(data_state['combined_data']):,} records"

        filtered = filter_data(
            data_state["combined_data"],
            facility=facility,
            well=well,
            well_status=well_status if include_well_status else None,
        )
        options = get_filter_options(data_state["combined_data"])

        if not metric or metric not in filtered.columns:
            chart_html = "<html><body></body></html>"
        else:
            chart_html = make_chart(
                filtered,
                metric,
                period,
                use_well_status=include_well_status,
            )

        result = (
            chart_html,
            status,
            options["facility"],
            options["well"],
        )
        if include_well_status:
            result += (options["well_status"],)
        return result
