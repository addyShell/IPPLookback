import pandas as pd

from dashboard.data_processing import load_data, prepare_data


def filter_from_date(data: pd.DataFrame, start: str) -> pd.DataFrame:
    if data.empty or "Date" not in data.columns:
        return data
    dates = pd.to_datetime(data["Date"], errors="coerce")
    if getattr(dates.dt, "tz", None) is not None:
        dates = dates.dt.tz_localize(None)
    return data[dates >= pd.Timestamp(start)]


def prepare_ipp_monthly(actuals: pd.DataFrame, forecasts: pd.DataFrame):
    data = prepare_data(actuals, forecasts)
    if "WellStatus" in data.columns:
        data = data.drop(columns=["WellStatus"])
    return filter_from_date(data, "2025-01-01")


def prepare_view_data(results: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    actuals = results.get("Actuals", pd.DataFrame())
    ipp_forecasts = results.get("IPP_Forecasts", pd.DataFrame())
    op_forecasts = results.get("OP_Forecasts", pd.DataFrame())
    weekly_actuals = results.get("Actuals_Weekly", pd.DataFrame())
    weekly_forecasts = results.get("IPP_Weekly_Forecasts", pd.DataFrame())
    return {
        "ipp_monthly": prepare_ipp_monthly(actuals, ipp_forecasts),
        "op": prepare_data(actuals, op_forecasts),
        "ipp_weekly": prepare_weekly(weekly_actuals, weekly_forecasts),
    }


def prepare_weekly(actuals: pd.DataFrame, forecasts: pd.DataFrame):
    data = prepare_data(actuals, forecasts)
    if "WellStatus" in data.columns:
        data = data.drop(columns=["WellStatus"])
    return filter_from_date(data, "2026-01-01")


def load_dashboard_data() -> dict[str, pd.DataFrame]:
    results = load_dashboard_results()
    return prepare_view_data(results)


def load_dashboard_results() -> dict[str, pd.DataFrame]:
    from SQL_ENDPT_GOM_PYTHON_CONNECT import load_results

    return load_results(names=(
        "Actuals",
        "IPP_Forecasts",
        "OP_Forecasts",
        "Actuals_Weekly",
        "IPP_Weekly_Forecasts",
    ))
