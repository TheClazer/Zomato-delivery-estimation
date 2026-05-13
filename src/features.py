"""Feature engineering."""
import numpy as np
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Works on pd.Series."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


def _parse_hm(s):
    """Convert 'HH:MM' or 'HH:MM:SS' string to minutes-of-day."""
    try:
        parts = str(s).split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError, TypeError):
        return np.nan


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Distance: most important feature
    df["distance_km"] = haversine_km(
        df["Restaurant_latitude"], df["Restaurant_longitude"],
        df["Delivery_location_latitude"], df["Delivery_location_longitude"]
    )
    # Food delivery >30km is physically implausible — NaN, don't drop (LightGBM handles NaN)
    df.loc[df["distance_km"] > 30, "distance_km"] = np.nan
    # Restaurant prep time = time picked - time ordered
    df["order_min"] = df["Time_Orderd"].apply(_parse_hm)
    df["picked_min"] = df["Time_Order_picked"].apply(_parse_hm)
    df["prep_time_min"] = df["picked_min"] - df["order_min"]
    # If negative, order crossed midnight: add 24h
    df.loc[df["prep_time_min"] < 0, "prep_time_min"] += 24 * 60
    # Time features
    df["order_hour"] = (df["order_min"] // 60).fillna(-1).astype(int)
    df["is_peak_lunch"] = df["order_hour"].between(11, 14).astype(int)
    df["is_peak_dinner"] = df["order_hour"].between(19, 22).astype(int)
    df["is_late_night"] = ((df["order_hour"] >= 22) |
                           (df["order_hour"] <= 5)).astype(int)
    df["is_weekend"] = (df["Order_Date"].dt.dayofweek >= 5).astype(int)
    df["day_of_week"] = df["Order_Date"].dt.dayofweek.fillna(-1).astype(int)
    df["month"] = df["Order_Date"].dt.month.fillna(-1).astype(int)
    return df


# Feature lists for modeling
NUMERIC_FEATURES = [
    "distance_km", "prep_time_min", "order_hour",
    "is_peak_lunch", "is_peak_dinner", "is_late_night", "is_weekend",
    "day_of_week", "month",
    "Delivery_person_Age", "Delivery_person_Ratings",
    "Vehicle_condition", "multiple_deliveries",
]
CATEGORICAL_FEATURES = [
    "Weather_conditions", "Road_traffic_density",
    "Type_of_vehicle", "Type_of_order", "City", "Festival",
]
TARGET = "Time_taken (min)"


def build_modeling_frame(df):
    """Return (X, y, cat_cols) ready for LightGBM."""
    df = add_features(df)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    for c in CATEGORICAL_FEATURES:
        X[c] = X[c].astype("category")
    y = df[TARGET].astype(float)
    return X, y, CATEGORICAL_FEATURES
