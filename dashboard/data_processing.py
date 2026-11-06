import pandas as pd

from SQL_ENDPT_GOM_PYTHON_CONNECT import load_results


def load_data(forecast_key: str = "OP_Forecasts") -> tuple[pd.DataFrame, pd.DataFrame]:
    results = load_results(names=("Actuals", forecast_key))
    return (
        results.get("Actuals", pd.DataFrame()),
        results.get(forecast_key, pd.DataFrame()),
    )


def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    results = load_results()
    actuals = results.get("Actuals", pd.DataFrame())
    ipp_forecasts = results.get("IPP_Forecasts", pd.DataFrame())
    op_forecasts = results.get("OP_Forecasts", pd.DataFrame())
    return (
        prepare_data(actuals, ipp_forecasts),
        prepare_data(actuals, op_forecasts),
    )


def prepare_data(actuals: pd.DataFrame, forecasts: pd.DataFrame) -> pd.DataFrame:
    frames = []
    status_by_well = {}

    if not actuals.empty:
        actuals = actuals.copy()
        actuals["Date"] = pd.to_datetime(actuals["PRODUCTION_DATETIME"])
        frames.append(actuals)

        if {"FACILITY_06_SHORT_NAME", "WellStatus"}.issubset(actuals.columns):
            status_by_well = (
                actuals[["FACILITY_06_SHORT_NAME", "WellStatus"]]
                .dropna()
                .groupby("FACILITY_06_SHORT_NAME", sort=False)["WellStatus"]
                .first()
                .to_dict()
            )

    if not forecasts.empty:
        forecasts = forecasts.copy()
        forecasts["Date"] = pd.to_datetime(forecasts["Prod Date"])
        if "FACILITY_06_SHORT_NAME" in forecasts.columns:
            forecasts["WellStatus"] = forecasts["FACILITY_06_SHORT_NAME"].map(status_by_well)
        frames.append(forecasts)

    if not frames:
        return pd.DataFrame()

    data = pd.concat(frames, ignore_index=True, sort=False)
    data["Year"] = data["Date"].dt.year
    data["Well"] = data["FACILITY_06_SHORT_NAME"].fillna("Unknown")
    data["Facility"] = data["BUSINESS_AREA_NAME"].fillna("Unknown")
    data["WellStatus"] = (
        data["WellStatus"].fillna("Unknown")
        if "WellStatus" in data.columns
        else "Unknown"
    )

    for volume in ("AFS", "SCH_DEF", "UNSCH_DEF"):
        if volume in data.columns:
            data[volume] = pd.to_numeric(data[volume], errors="coerce").fillna(0.0)

    if {"AFS", "SCH_DEF", "UNSCH_DEF"}.issubset(data.columns):
        data["SUBSURFACE"] = data["AFS"] + data["SCH_DEF"] + data["UNSCH_DEF"]

    return data


def selected_values(value) -> list:
    if not value:
        return []
    return value if isinstance(value, list) else [value]


def filter_data(
    data: pd.DataFrame,
    facility=None,
    well=None,
    well_status=None,
) -> pd.DataFrame:
    filtered = data.copy() if not data.empty else data
    facilities = selected_values(facility)
    wells = selected_values(well)
    statuses = selected_values(well_status)

    if not filtered.empty and facilities:
        filtered = filtered[filtered["Facility"].isin(facilities)]
    if not filtered.empty and wells:
        filtered = filtered[filtered["Well"].isin(wells)]
    if not filtered.empty and statuses:
        filtered = filtered[filtered["WellStatus"].isin(statuses)]

    return filtered


def get_filter_options(data: pd.DataFrame) -> dict[str, list[str]]:
    if data.empty:
        return {"facility": [], "well": [], "well_status": []}
    return {
        "facility": sorted(data["Facility"].dropna().unique().tolist()),
        "well": sorted(data["Well"].dropna().unique().tolist()),
        "well_status": sorted(data["WellStatus"].dropna().unique().tolist()),
    }


def get_default_filter_values(data: pd.DataFrame) -> dict[str, list[str]]:
    options = get_filter_options(data)
    excluded_facilities = {"DW Mature Asset NOV Other", "Na Kika"}

    excluded_statuses = {"Unknown"}
    excluded_statuses.update(
        status for status in options["well_status"]
        if str(status).replace(" ", "").replace("_", "").lower() == "noafs"
    )

    return {
        "facility": [
            facility for facility in options["facility"]
            if facility not in excluded_facilities
        ],
        "well": [],
        "well_status": [
            status for status in options["well_status"]
            if status not in excluded_statuses
        ],
    }


def get_metric_options(data: pd.DataFrame) -> list[dict[str, str]]:
    available_metrics = ("AFS", "IPSC", "SCH_DEF", "UNSCH_DEF", "SUBSURFACE")
    return [
        {"label": metric, "value": metric}
        for metric in available_metrics
        if metric in data.columns
    ]
