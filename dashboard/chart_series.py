import pandas as pd
from bokeh.models import ColumnDataSource

from dashboard.chart_format import status_sort_key, forecast_year
from dashboard.colours import (
    SHELL_BROWN,
    SHELL_MID_BLUE,
    SHELL_VERY_DARK_GREY,
    SHELL_YELLOW,
)


def add_actual_series(
    plot,
    actuals: pd.DataFrame,
    metric: str,
    period_column: str,
    use_well_status: bool,
    forecast_colours: dict,
):
    renderers = []
    x_is_datetime = period_column == "Period"

    if use_well_status and not actuals.empty and "WellStatus" in actuals.columns:
        actuals["WellStatus"] = actuals["WellStatus"].replace("NFA", "NFA20")
        actuals["WellStatus"] = actuals["WellStatus"].replace("NFAOP20", "NFA20")
        actuals["WellStatus"] = actuals["WellStatus"].map(
            lambda value: str(value).replace("NewOP", "New")
        )
        status_names = sorted(
            actuals["WellStatus"].fillna("Unknown").unique(),
            key=status_sort_key,
        )
        bottoms = {}
        for status_name in status_names:
            status_actuals = actuals[actuals["WellStatus"] == status_name].sort_values(period_column)
            numeric_values = pd.to_numeric(status_actuals[metric], errors="coerce")
            status_actuals = status_actuals[numeric_values.notna() & (numeric_values != 0)]
            if status_actuals.empty:
                continue

            if status_name in {"NFA20", "NFAOP20", "NFA"}:
                colour = SHELL_YELLOW
            elif status_name.startswith("New"):
                status_year = status_name.removeprefix("New").removeprefix("OP")
                colour = forecast_colours.get(status_year, SHELL_MID_BLUE)
            elif status_name.replace(" ", "").upper() == "NOAFS":
                colour = SHELL_VERY_DARK_GREY
            else:
                colour = SHELL_BROWN

            x_values = status_actuals[period_column].tolist()
            bottom_values = [bottoms.get(value, 0.0) for value in x_values]
            top_values = [
                bottom + value
                for bottom, value in zip(bottom_values, status_actuals[metric].tolist())
            ]
            for value, top in zip(x_values, top_values):
                bottoms[value] = top

            source = ColumnDataSource(dict(
                x=x_values,
                bottom=bottom_values,
                top=top_values,
                value=status_actuals[metric].tolist(),
                period=[
                    value.strftime("%b %Y") if hasattr(value, "strftime") else str(value)
                    for value in x_values
                ],
                label=[f"Actuals · {status_name}" for _ in x_values],
            ))
            renderer = plot.vbar(
                x="x", bottom="bottom", top="top",
                width=0.75 if not x_is_datetime else 20 * 24 * 60 * 60 * 1000,
                source=source, color=colour, alpha=0.35,
                line_color=SHELL_VERY_DARK_GREY,
                legend_label=f"Actuals · {status_name}",
            )
            renderers.append((f"Actuals · {status_name}", renderer))
    elif not actuals.empty:
        numeric_values = pd.to_numeric(actuals[metric], errors="coerce")
        actuals = actuals[numeric_values.notna() & (numeric_values != 0)]
        if not actuals.empty:
            x_values = actuals[period_column].tolist()
            source = ColumnDataSource(dict(
                x=x_values,
                top=actuals[metric].tolist(),
                value=actuals[metric].tolist(),
                period=[
                    value.strftime("%b %Y") if hasattr(value, "strftime") else str(value)
                    for value in x_values
                ],
                label=["Actuals" for _ in x_values],
            ))
            renderer = plot.vbar(
                x="x", top="top",
                width=0.75 if not x_is_datetime else 20 * 24 * 60 * 60 * 1000,
                source=source, color=SHELL_YELLOW, alpha=0.35,
                line_color=SHELL_VERY_DARK_GREY, legend_label="Actuals",
            )
            renderers.append(("Actuals", renderer))
    return renderers


def add_forecast_series(
    plot,
    forecasts: pd.DataFrame,
    forecast_names: list[str],
    metric: str,
    period_column: str,
    forecast_colours: dict,
):
    renderers = []
    for forecast_name in forecast_names:
        forecast = forecasts[forecasts["Forecast"] == forecast_name].sort_values(period_column)
        numeric_values = pd.to_numeric(forecast[metric], errors="coerce")
        forecast = forecast[numeric_values.notna() & (numeric_values != 0)]
        if forecast.empty:
            continue

        colour = forecast_colours.get(
            forecast_year(str(forecast_name)) or str(forecast_name),
            SHELL_MID_BLUE,
        )
        source = ColumnDataSource(dict(
            x=forecast[period_column].tolist(),
            y=forecast[metric].tolist(),
            value=forecast[metric].tolist(),
            period=[
                value.strftime("%b %Y") if hasattr(value, "strftime") else str(value)
                for value in forecast[period_column].tolist()
            ],
            label=[str(forecast_name) for _ in forecast[period_column]],
        ))
        renderer = plot.line(
            x="x", y="y", source=source, line_color=colour,
            line_width=3, legend_label=str(forecast_name),
        )
        plot.scatter(
            x="x", y="y", source=source, size=8,
            color=colour, legend_label=str(forecast_name),
        )
        renderers.append((str(forecast_name), renderer))
    return renderers
