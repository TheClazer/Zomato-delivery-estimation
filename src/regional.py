"""Region labelling for the Zomato delivery dataset.

Derives a North/South India label for each order from the city code
embedded in ``Delivery_person_ID`` (e.g. ``KOCRES16DEL01`` → Kochi).
Falls back to a latitude/longitude bounding-box check for any rows
whose city prefix we don't recognise.

South = Kerala, Tamil Nadu, Andhra Pradesh, Telangana, Karnataka.
Everything else (including Maharashtra, Goa, West Bengal, etc.) = North,
per the team's brief.
"""
from __future__ import annotations
import re
import numpy as np
import pandas as pd

# ---- city code → (city, state, region) -----------------------------------
CITY_CODE_MAP: dict[str, tuple[str, str, str]] = {
    # South — 6 cities
    "BANG":   ("Bangalore",  "Karnataka",       "South"),
    "MYS":    ("Mysore",     "Karnataka",       "South"),
    "CHEN":   ("Chennai",    "Tamil Nadu",      "South"),
    "COIMB":  ("Coimbatore", "Tamil Nadu",      "South"),
    "HYD":    ("Hyderabad",  "Telangana",       "South"),
    "KOC":    ("Kochi",      "Kerala",          "South"),
    # North — 16 cities (Goa folded into North per spec)
    "JAP":    ("Jaipur",     "Rajasthan",       "North"),
    "RANCHI": ("Ranchi",     "Jharkhand",       "North"),
    "SUR":    ("Surat",      "Gujarat",         "North"),
    "MUM":    ("Mumbai",     "Maharashtra",     "North"),
    "VAD":    ("Vadodara",   "Gujarat",         "North"),
    "INDO":   ("Indore",     "Madhya Pradesh",  "North"),
    "PUNE":   ("Pune",       "Maharashtra",     "North"),
    "AGR":    ("Agra",       "Uttar Pradesh",   "North"),
    "LUDH":   ("Ludhiana",   "Punjab",          "North"),
    "KNP":    ("Kanpur",     "Uttar Pradesh",   "North"),
    "ALH":    ("Allahabad",  "Uttar Pradesh",   "North"),
    "DEH":    ("Dehradun",   "Uttarakhand",     "North"),
    "GOA":    ("Goa",        "Goa",             "North"),
    "AURG":   ("Aurangabad", "Maharashtra",     "North"),
    "KOL":    ("Kolkata",    "West Bengal",     "North"),
    "BHP":    ("Bhopal",     "Madhya Pradesh",  "North"),
}

# Approximate centroid of each known city (lat, lon). Used to cross-check
# the code mapping and to back-fill unknown rows from coordinates alone.
CITY_CENTROIDS: dict[str, tuple[float, float]] = {
    "BANG":   (12.97, 77.59),
    "MYS":    (12.30, 76.65),
    "CHEN":   (13.08, 80.27),
    "COIMB":  (11.02, 76.96),
    "HYD":    (17.39, 78.49),
    "KOC":    (9.93,  76.27),
    "JAP":    (26.92, 75.79),
    "RANCHI": (23.34, 85.31),
    "SUR":    (21.17, 72.83),
    "MUM":    (19.08, 72.88),
    "VAD":    (22.31, 73.18),
    "INDO":   (22.72, 75.86),
    "PUNE":   (18.52, 73.86),
    "AGR":    (27.18, 78.01),
    "LUDH":   (30.90, 75.86),
    "KNP":    (26.45, 80.33),
    "ALH":    (25.43, 81.85),
    "DEH":    (30.32, 78.03),
    "GOA":    (15.30, 74.12),
    "AURG":   (19.88, 75.34),
    "KOL":    (22.57, 88.36),
    "BHP":    (23.26, 77.40),
}

SOUTH_STATES = {"Kerala", "Tamil Nadu", "Andhra Pradesh", "Telangana", "Karnataka"}


def extract_city_code(delivery_person_id: pd.Series) -> pd.Series:
    """Pull the alphabetical prefix from rider IDs like ``KOCRES16DEL01``."""
    return delivery_person_id.astype(str).str.extract(r"^([A-Z]+)RES",
                                                       expand=False)


def _classify_by_coords(lat: float, lon: float) -> str:
    """Bounding-box fallback when city code is unknown."""
    if pd.isna(lat) or pd.isna(lon) or abs(lat) < 1 or abs(lon) < 1:
        return "Unknown"
    # South Indian states roughly span lat 8–19, lon 74–84 (Kerala to AP coast)
    if 8.0 <= lat <= 19.0 and 74.0 <= lon <= 84.5:
        return "South"
    if 18.0 <= lat <= 32.0 and 68.0 <= lon <= 89.0:
        return "North"
    return "Unknown"


def annotate_region(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``city_code``, ``city``, ``state``, ``region`` columns.

    Code → region is the primary path. Coord fallback only runs on rows
    whose prefix is missing. Rows that remain ``Unknown`` after both
    paths are flagged so callers can drop them from training data.
    """
    df = df.copy()
    df["city_code"] = extract_city_code(df["Delivery_person_ID"])

    def _lookup(code):
        if isinstance(code, str) and code in CITY_CODE_MAP:
            return CITY_CODE_MAP[code]
        return (np.nan, np.nan, np.nan)

    df[["city", "state", "region"]] = df["city_code"].apply(
        lambda c: pd.Series(_lookup(c)))

    # Fallback by coordinates for any unmapped rows
    needs_coord = df["region"].isna()
    if needs_coord.any():
        coord_region = df.loc[needs_coord].apply(
            lambda r: _classify_by_coords(r.get("Restaurant_latitude"),
                                           r.get("Restaurant_longitude")),
            axis=1)
        df.loc[needs_coord, "region"] = coord_region

    df["is_south"] = (df["region"] == "South").astype(int)
    return df


def coord_consistency_check(df: pd.DataFrame) -> pd.DataFrame:
    """For each known city code, compare the median lat/lon of its rows
    to the expected centroid. Distance > 250 km is a red flag.

    Returns a DataFrame with one row per city: code, n, median_lat,
    median_lon, expected_lat, expected_lon, km_off, ok.
    """
    df = df.copy()
    if "city_code" not in df.columns:
        df["city_code"] = extract_city_code(df["Delivery_person_ID"])

    rows = []
    for code, (clat, clon) in CITY_CENTROIDS.items():
        sub = df[df["city_code"] == code]
        if len(sub) == 0:
            continue
        med_lat = pd.to_numeric(sub["Restaurant_latitude"], errors="coerce").median()
        med_lon = pd.to_numeric(sub["Restaurant_longitude"], errors="coerce").median()
        km_off = _haversine(med_lat, med_lon, clat, clon)
        rows.append({
            "code": code,
            "city": CITY_CODE_MAP[code][0],
            "state": CITY_CODE_MAP[code][1],
            "region": CITY_CODE_MAP[code][2],
            "n_orders": int(len(sub)),
            "median_lat": round(med_lat, 3) if pd.notna(med_lat) else None,
            "median_lon": round(med_lon, 3) if pd.notna(med_lon) else None,
            "expected_lat": clat,
            "expected_lon": clon,
            "km_off": round(km_off, 1) if pd.notna(km_off) else None,
            "ok": bool(pd.notna(km_off) and km_off < 250),
        })
    return pd.DataFrame(rows).sort_values("km_off", ascending=False)


def _haversine(lat1, lon1, lat2, lon2) -> float:
    if any(pd.isna(x) for x in (lat1, lon1, lat2, lon2)):
        return np.nan
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))
