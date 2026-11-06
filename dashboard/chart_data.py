import calendar

import pandas as pd


def yearly_total_per_calendar_day(
    data: pd.DataFrame,
    metric: str,
    forecast_only: bool = False,
) -> pd.DataFrame:
    if data.empty or metric not in data.columns:
        return pd.DataFrame()

    subset = data.copy()
    if forecast_only:
        subset = subset[subset["Forecast"] != "Actuals"]
        group_columns = ["Year", "Forecast"]
    else:
        subset = subset[subset["Forecast"] == "Actuals"]
        if "WellStatus" in subset.columns:
            subset["WellStatus"] = subset["WellStatus"].fillna("Unknown")
            group_columns = ["Year", "WellStatus"]
        else:
            group_columns = ["Year"]

    subset[metric] = pd.to_numeric(subset[metric], errors="coerce")
    result = subset.groupby(group_columns, as_index=False)[metric].sum()
    if result.empty:
        return result

    def divide_by_calendar_days(row):
        year = int(row["Year"])
        leap_year = year % 400 == 0 or (year % 100 != 0 and year % 4 == 0)
        return row[metric] / (366.0 if leap_year else 365.0)

    result[metric] = result.apply(divide_by_calendar_days, axis=1) / 1000.0
    return result


def monthly_total_per_calendar_day(
    data: pd.DataFrame,
    metric: str,
    forecast_only: bool = False,
) -> pd.DataFrame:
    if data.empty or metric not in data.columns or "Date" not in data.columns:
        return pd.DataFrame()

    subset = data.copy()
    if forecast_only:
        subset = subset[subset["Forecast"] != "Actuals"]
        group_columns = ["Period", "Forecast"]
    else:
        subset = subset[subset["Forecast"] == "Actuals"]
        group_columns = ["Period", "WellStatus"] if "WellStatus" in subset.columns else ["Period"]

    subset[metric] = pd.to_numeric(subset[metric], errors="coerce")
    dates = pd.to_datetime(subset["Date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    subset["Period"] = dates.dt.to_period("M").dt.to_timestamp()
    if not forecast_only and "WellStatus" in subset.columns:
        subset["WellStatus"] = subset["WellStatus"].fillna("Unknown")

    result = subset.groupby(group_columns, as_index=False)[metric].sum(min_count=1)
    if result.empty:
        return result

    result[metric] = result.apply(
        lambda row: row[metric] / calendar.monthrange(
            int(row["Period"].year), int(row["Period"].month)
        )[1] / 1000.0,
        axis=1,
    )
    return result


def weekly_total_per_calendar_day(
    data: pd.DataFrame,
    metric: str,
    forecast_only: bool = False,
) -> pd.DataFrame:
    if data.empty or metric not in data.columns or "Date" not in data.columns:
        return pd.DataFrame()

    subset = data.copy()
    if forecast_only:
        subset = subset[subset["Forecast"] != "Actuals"]
        group_columns = ["Week", "Forecast"]
    else:
        subset = subset[subset["Forecast"] == "Actuals"]
        group_columns = (
            ["Week", "WellStatus"]
            if "WellStatus" in subset.columns else ["Week"]
        )

    subset[metric] = pd.to_numeric(subset[metric], errors="coerce")
    dates = pd.to_datetime(subset["Date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    subset["Week"] = dates - pd.to_timedelta(dates.dt.weekday, unit="D")

    if not forecast_only and "WellStatus" in subset.columns:
        subset["WellStatus"] = subset["WellStatus"].fillna("Unknown")

    result = subset.groupby(group_columns, as_index=False)[metric].sum(min_count=1)
    if not result.empty:
        result[metric] = result[metric] / 7.0 / 1000.0
    return result
