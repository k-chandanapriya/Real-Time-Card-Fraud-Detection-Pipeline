import numpy as np
import pandas as pd

CATEGORICAL = ["category", "gender"]


def haversine_km(lat1, lon1, lat2, lon2):
    # distance between the cardholder and the merchant
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def build_features(df):
    ts = pd.to_datetime(df["trans_date_trans_time"])
    dob = pd.to_datetime(df["dob"])

    return pd.DataFrame({
        "amt": df["amt"],
        "city_pop": df["city_pop"],
        "hour": ts.dt.hour,  # a lot of fraud happens late at night
        "age": (ts - dob).dt.days // 365,
        "distance_km": haversine_km(df["lat"], df["long"], df["merch_lat"], df["merch_long"]),
        "category": df["category"],
        "gender": df["gender"],
    })
