import json
import math

import pandas as pd

from dashboard.chart_data import monthly_total_per_calendar_day


def build_percentage_table(
    data: pd.DataFrame,
    metric: str,
    month_count: int | None = 6,
) -> tuple[list[pd.Timestamp], list[dict]]:
    actuals = monthly_total_per_calendar_day(data, metric, forecast_only=False)
    forecasts = monthly_total_per_calendar_day(data, metric, forecast_only=True)
    if actuals.empty and forecasts.empty:
        return [], []

    all_periods = pd.concat([
        actuals["Period"] if not actuals.empty else pd.Series(dtype="datetime64[ns]"),
        forecasts["Period"] if not forecasts.empty else pd.Series(dtype="datetime64[ns]"),
    ], ignore_index=True).dropna()
    if all_periods.empty:
        return [], []

    latest = pd.to_datetime(all_periods.max()).to_period("M").start_time
    first = (
        pd.to_datetime(all_periods.min()).to_period("M").start_time
        if month_count is None
        else latest - pd.DateOffset(months=month_count - 1)
    )
    visible_months = list(pd.date_range(first, latest, freq="MS"))
    actual_lookup = (
        actuals.groupby("Period", as_index=False)[metric].sum().set_index("Period")[metric].to_dict()
        if not actuals.empty else {}
    )

    rows = []
    if actual_lookup:
        actual_values = {
            month: (
                "100%" if pd.notna(actual_lookup.get(month))
                and math.isfinite(float(actual_lookup.get(month)))
                and float(actual_lookup.get(month)) != 0 else "—"
            )
            for month in visible_months
        }
        rows.append({"label": "Actuals", **actual_values})

    if not forecasts.empty:
        for forecast_name in sorted(forecasts["Forecast"].dropna().unique(), reverse=True):
            forecast = forecasts[forecasts["Forecast"] == forecast_name]
            lookup = forecast.set_index("Period")[metric].to_dict()
            cells = {}
            has_finite_value = False
            for month in visible_months:
                forecast_value = lookup.get(month)
                actual_value = actual_lookup.get(month)
                if pd.notna(forecast_value) and math.isfinite(float(forecast_value)):
                    has_finite_value = True
                cells[month] = (
                    f"{float(forecast_value) / float(actual_value) * 100:.1f}%"
                    if pd.notna(forecast_value) and pd.notna(actual_value)
                    and float(actual_value) != 0 else "—"
                )
            if has_finite_value:
                rows.append({"label": str(forecast_name), **cells})
    return visible_months, rows


def serialize_percentage_table(
    visible_months: list[pd.Timestamp],
    table_rows: list[dict],
) -> str:
    serializable_rows = []
    for row in table_rows:
        cells = {
            str(month.to_period("M")): value
            for month, value in row.items()
            if isinstance(month, pd.Timestamp)
        }
        serializable_rows.append({"label": row["label"], "cells": cells})

    table_months = [
        {"key": str(month.to_period("M")), "timestamp": month.value // 1_000_000}
        for month in visible_months
    ]
    return json.dumps({"months": table_months, "rows": serializable_rows})
