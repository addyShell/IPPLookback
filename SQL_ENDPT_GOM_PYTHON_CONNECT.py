from pathlib import Path

import pandas as pd
from databricks import sql

SERVER_HOSTNAME = "adb-4015501114256393.13.azuredatabricks.net"
HTTP_PATH = "/sql/1.0/warehouses/608ce64ef8937b4a"

SCRIPT_DIR = Path(__file__).resolve().parent
QUERY_FILES = {
    "Actuals": SCRIPT_DIR / "actuals_databricks.sql",
    "OP_Forecasts": SCRIPT_DIR / "op_forecasts_databricks.sql",
    "IPP_Forecasts": SCRIPT_DIR / "ipp_forecasts_databricks.sql",
    "Actuals_Weekly": SCRIPT_DIR / "actuals_weekly_databricks.sql",
    "IPP_Weekly_Forecasts": SCRIPT_DIR / "ipp_weekly_forecasts_databricks.sql",
}


def load_query(path: Path) -> str:
    # The Databricks connector expects a single statement without a trailing semicolon.
    return path.read_text(encoding="utf-8").strip().rstrip(";")


def run_query(connection, name: str, query: str) -> pd.DataFrame:
    print(f"Running {name} query...")
    with connection.cursor() as cursor:
        cursor.execute(query)
        df = cursor.fetchall_arrow().to_pandas()
    print(f"  {name}: {len(df):,} rows, {len(df.columns)} columns")
    return df


def load_results(names=None):
    results = {}
    query_names = list(QUERY_FILES)
    if names is not None:
        requested_names = list(names)
        query_names = [
            name for name in query_names
            if name in requested_names
        ]
        unknown_names = [
            name for name in requested_names
            if name not in QUERY_FILES
        ]
        if unknown_names:
            raise ValueError(f"Unknown query names: {', '.join(unknown_names)}")

    # OAuth U2M: opens a browser to sign in via https://<workspace>/oidc; tokens are cached locally.
    with sql.connect(
        server_hostname=SERVER_HOSTNAME,
        http_path=HTTP_PATH,
        auth_type="databricks-oauth",
    ) as connection:
        for name in query_names:
            path = QUERY_FILES[name]
            try:
                results[name] = run_query(connection, name, load_query(path))
            except Exception as exc:
                print(f"  {name} failed: {exc}")
    return results


def main():
    results = load_results()

    if not results:
        print("No query results returned.")
        return results

    for name, df in results.items():
        print(f"\n===== {name} =====")
        print(df.head(20).to_string(index=False))
        print(f"... {len(df):,} total rows")
        df.info()

    return results


if __name__ == "__main__":
    results = main()
    actuals_df = results.get("Actuals")
    op_forecasts_df = results.get("OP_Forecasts")