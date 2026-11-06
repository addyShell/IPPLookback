import pandas as pd
from bokeh.embed import file_html
from bokeh.resources import INLINE

from dashboard.chart_data import (
    monthly_total_per_calendar_day,
    weekly_total_per_calendar_day,
    yearly_total_per_calendar_day,
)
from dashboard.chart_format import build_forecast_colour_map
from dashboard.chart_plot import (
    add_chart_legends,
    configure_month_axis,
    configure_week_axis,
    create_plot,
)
from dashboard.chart_series import add_actual_series, add_forecast_series
from dashboard.chart_table import (
    build_percentage_table,
    serialize_percentage_table,
)
from dashboard.chart_table_script import percentage_table_script


def make_chart(
    data: pd.DataFrame,
    metric: str,
    period: str = "year",
    use_well_status: bool = True,
) -> str:
    chart_data = data.copy() if data is not None else data
    if not use_well_status and chart_data is not None and "WellStatus" in chart_data.columns:
        chart_data = chart_data.drop(columns=["WellStatus"])

    if period == "month":
        actuals = monthly_total_per_calendar_day(chart_data, metric, forecast_only=False)
        forecasts = monthly_total_per_calendar_day(chart_data, metric, forecast_only=True)
        period_column = "Period"
    elif period == "week":
        actuals = weekly_total_per_calendar_day(chart_data, metric, forecast_only=False)
        forecasts = weekly_total_per_calendar_day(chart_data, metric, forecast_only=True)
        period_column = "Week"
    else:
        actuals = yearly_total_per_calendar_day(chart_data, metric, forecast_only=False)
        forecasts = yearly_total_per_calendar_day(chart_data, metric, forecast_only=True)
        period_column = "Year"

    forecast_names = (
        sorted(forecasts["Forecast"].dropna().unique(), reverse=True)
        if not forecasts.empty else []
    )
    forecast_colours = build_forecast_colour_map(forecast_names)
    plot = create_plot(metric, period)

    actual_renderers = add_actual_series(
        plot, actuals, metric, period_column, use_well_status, forecast_colours
    )
    forecast_renderers = add_forecast_series(
        plot, forecasts, forecast_names, metric, period_column, forecast_colours
    )
    add_chart_legends(plot, actual_renderers, forecast_renderers)

    if period == "month":
        configure_month_axis(plot, actuals, forecasts, period_column)
    elif period == "week":
        configure_week_axis(plot, actuals, forecasts, period_column)

    chart_html = file_html(plot, INLINE, title=f"{metric} Lookback")
    chart_html = chart_html.replace(
        "</head>",
        '<meta name="viewport" content="width=device-width, initial-scale=1"></head>',
    )
    if period == "year":
        return chart_html

    if period == "week":
        from dashboard.chart_table import (
            build_weekly_percentage_table,
            serialize_weekly_percentage_table,
        )
        visible_weeks, table_rows = build_weekly_percentage_table(
            chart_data, metric, week_count=None
        )
        table_json = serialize_weekly_percentage_table(visible_weeks, table_rows)
    else:
        visible_months, table_rows = build_percentage_table(
            chart_data, metric, month_count=None
        )
        table_json = serialize_percentage_table(visible_months, table_rows)
    chart_html = chart_html.replace(
        "</body>",
        percentage_table_script(table_json) + "</body>",
    )
    return chart_html
