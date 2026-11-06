import pandas as pd
from bokeh.models import (
    DatetimeTickFormatter,
    FixedTicker,
    HoverTool,
    Legend,
    LegendItem,
)
from bokeh.plotting import figure

from dashboard.colours import (
    SHELL_PALE_GREY,
    SHELL_VERY_DARK_GREY,
    SHELL_WHITE,
)


def create_plot(metric: str, period: str) -> object:
    axis_labels = {
        "month": "Month",
        "week": "Week starting Monday",
        "year": "Year",
    }
    title_suffix = (
        "Monthly total divided by calendar days"
        if period == "month"
        else "Weekly total divided by seven days"
        if period == "week"
        else "Yearly total divided by calendar days"
    )
    plot = figure(
        width=1000,
        height=480,
        title=f"{metric} - {title_suffix}",
        x_axis_label=axis_labels.get(period, "Year"),
        y_axis_label="kbpd",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        active_scroll="wheel_zoom",
        background_fill_color=SHELL_WHITE,
        border_fill_color=SHELL_WHITE,
        sizing_mode="stretch_width",
    )
    plot.xgrid.grid_line_color = SHELL_PALE_GREY
    plot.ygrid.grid_line_color = SHELL_PALE_GREY
    plot.outline_line_color = SHELL_VERY_DARK_GREY
    plot.title.text_color = SHELL_VERY_DARK_GREY
    plot.xaxis.axis_line_color = SHELL_VERY_DARK_GREY
    plot.yaxis.axis_line_color = SHELL_VERY_DARK_GREY
    plot.add_tools(HoverTool(
        tooltips=[
            ("Series", "@label"),
            ("Period", "@period"),
            (metric, "@value{0,0.0} kbpd"),
        ],
        mode="mouse",
    ))
    return plot


def add_chart_legends(plot, actual_renderers: list, forecast_renderers: list):
    for legend_name in list(plot.select(type=Legend)):
        plot.center.remove(legend_name)
    if actual_renderers:
        plot.add_layout(Legend(
            items=[
                LegendItem(label=label, renderers=[renderer])
                for label, renderer in actual_renderers
            ],
            title="Actuals",
            orientation="horizontal",
            location="center",
            label_text_color=SHELL_VERY_DARK_GREY,
            background_fill_alpha=0,
            border_line_alpha=0,
        ), "below")
    if forecast_renderers:
        plot.add_layout(Legend(
            items=[
                LegendItem(label=label, renderers=[renderer])
                for label, renderer in forecast_renderers
            ],
            title="Forecasts",
            orientation="horizontal",
            location="center",
            label_text_color=SHELL_VERY_DARK_GREY,
            background_fill_alpha=0,
            border_line_alpha=0,
        ), "below")


def configure_month_axis(plot, actuals: pd.DataFrame, forecasts: pd.DataFrame, period_column: str):
    plot.xaxis[0].formatter = DatetimeTickFormatter(months="%b %Y")
    if actuals.empty and forecasts.empty:
        return
    frames = [
        frame[period_column] for frame in (actuals, forecasts) if not frame.empty
    ]
    all_dates = pd.concat(frames, ignore_index=True)
    parsed_dates = pd.to_datetime(all_dates).dropna()
    if parsed_dates.empty:
        return
    latest = parsed_dates.max()
    plot.x_range.start = (latest - pd.DateOffset(months=11)).value // 1_000_000
    plot.x_range.end = latest.value // 1_000_000
    first_month = parsed_dates.min().to_period("M").start_time
    last_month = parsed_dates.max().to_period("M").start_time
    month_starts = pd.date_range(first_month, last_month, freq="MS")
    plot.xaxis.ticker = FixedTicker(
        ticks=[timestamp.value // 1_000_000 for timestamp in month_starts]
    )


def configure_week_axis(
    plot,
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
    period_column: str,
):
    plot.xaxis[0].formatter = DatetimeTickFormatter(days="%d %b %Y", months="%d %b %Y")
    if actuals.empty and forecasts.empty:
        return
    frames = [
        frame[period_column] for frame in (actuals, forecasts) if not frame.empty
    ]
    parsed_dates = pd.to_datetime(pd.concat(frames, ignore_index=True)).dropna()
    if parsed_dates.empty:
        return
    latest = parsed_dates.max()
    earliest = parsed_dates.min()
    visible_start = latest - pd.Timedelta(weeks=11)
    plot.x_range.start = max(visible_start, earliest).value // 1_000_000
    plot.x_range.end = latest.value // 1_000_000
    week_starts = pd.date_range(earliest, latest, freq="W-MON")
    plot.xaxis.ticker = FixedTicker(
        ticks=[timestamp.value // 1_000_000 for timestamp in week_starts]
    )
