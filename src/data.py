"""Clean loader for the Zomato delivery dataset."""
import numpy as np
import pandas as pd


def load_clean(path: str) -> pd.DataFrame:
    """Load and clean the raw Zomato CSV. Returns ready-to-feature DataFrame."""
    df = pd.read_csv(path)
    # 1. Strip whitespace + replace 'NaN' strings with real NaN
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"NaN": np.nan, "nan": np.nan, "": np.nan})
    # 2. Target: coerce to numeric
    if "Time_taken (min)" in df.columns:
        df["Time_taken (min)"] = pd.to_numeric(df["Time_taken (min)"],
                                               errors="coerce")
    # 3. Weather: strip "conditions " prefix
    if "Weather_conditions" in df.columns:
        df["Weather_conditions"] = (df["Weather_conditions"].astype(str)
                                      .str.replace("conditions", "", regex=False)
                                      .str.strip())
    # 4. Coerce numeric columns
    num_cols = ["Delivery_person_Age", "Delivery_person_Ratings",
                "Restaurant_latitude", "Restaurant_longitude",
                "Delivery_location_latitude", "Delivery_location_longitude",
                "Vehicle_condition", "multiple_deliveries"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # 5. Parse the order date
    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date"],
                                          errors="coerce", dayfirst=True)
    # 6. Drop rows missing the target
    df = df.dropna(subset=["Time_taken (min)"]).reset_index(drop=True)
    # 7. Cap impossible ratings
    if "Delivery_person_Ratings" in df.columns:
        df.loc[df["Delivery_person_Ratings"] > 5,
               "Delivery_person_Ratings"] = np.nan
    # 8. Drop bad coordinates (zero island)
    cc = ["Restaurant_latitude", "Restaurant_longitude",
          "Delivery_location_latitude", "Delivery_location_longitude"]
    if all(c in df.columns for c in cc):
        mask = (df[cc].abs() > 1).all(axis=1)
        df = df[mask].reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = load_clean("data/raw/Zomato Dataset.csv")
    print("Shape:", df.shape)
    print("\nMissingness:")
    print(df.isna().sum().sort_values(ascending=False).head(10))
    print("\nTarget stats:")
    print(df["Time_taken (min)"].describe())
    df.to_parquet("data/processed/train.parquet")
    print("\nSaved to data/processed/train.parquet")
