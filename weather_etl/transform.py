import pandas as pd


def transform_data(df):
    df["time"] = pd.to_datetime(df["time"])
    df.rename(
        columns={
            "time": "timestamp",
            "temperature_2m": "temperature_C",
            "precipitation": "precip_mm",
        },
        inplace=True,
    )
    return df
