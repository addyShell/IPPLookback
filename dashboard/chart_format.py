import re

from dashboard.colours import (
    FORECAST_COLOURS,
    SHELL_BROWN,
    SHELL_DARK_GREEN,
    SHELL_MID_BLUE,
    SHELL_ORANGE,
    SHELL_PURPLE,
    SHELL_RED,
)


def status_sort_key(status_name: str) -> tuple[int, int, str]:
    status_name = str(status_name)
    normalized_status = status_name.replace("NFAOP20", "NFA20").replace("NewOP", "New")
    if normalized_status in {"NFA20", "NFA"}:
        return (0, 0, status_name)

    new_match = re.fullmatch(r"New(\d{2})", normalized_status)
    if new_match:
        return (1, int(new_match.group(1)), status_name)

    if normalized_status.replace(" ", "").upper() == "NOAFS":
        return (2, 0, status_name)

    return (3, 0, status_name)


def forecast_year(forecast_name: str) -> str | None:
    match = re.search(r"OP(\d{2})", str(forecast_name))
    return match.group(1) if match else None


def build_forecast_colour_map(forecast_names: list[str]) -> dict[str | None, str]:
    named_op_colours = {
        "20": SHELL_ORANGE,
        "21": SHELL_DARK_GREEN,
        "22": SHELL_RED,
        "23": SHELL_PURPLE,
        "24": SHELL_MID_BLUE,
        "25": SHELL_BROWN,
    }
    colour_map = {
        forecast_year(str(name)): named_op_colours.get(forecast_year(str(name)))
        for name in forecast_names
        if forecast_year(str(name)) in named_op_colours
    }
    remaining_names = [
        str(name) for name in forecast_names if forecast_year(str(name)) is None
    ]
    for index, forecast_name in enumerate(remaining_names):
        colour_map[forecast_name] = FORECAST_COLOURS[index % len(FORECAST_COLOURS)]
    return colour_map
