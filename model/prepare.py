"""WFP Uganda food prices -> tidy monthly retail series for maize and beans.

Input:  data/raw/wfp_food_prices_uga.csv (WFP via HDX, CC BY-IGO)
Output: data/processed/monthly.csv  one row per (crop, market, month) observed
        columns: month, crop, market, admin1, lat, lon, price (UGX/kg retail), commodity

Rules (docs/BUILD_PLAN.md, workstream A):
- Retail, KG, UGX only (wholesale series ended 2022).
- crop=maize from "Maize (white)" (2011-) and "Maize" (2010-2018); when both exist
  for the same market-month, keep "Maize (white)".
- crop=beans from "Beans".
- Town markets only: drop any market containing "refugee settlement".
- Drop entry errors: a price more than OUTLIER_FACTOR x away from the median of
  the same series' other observations within +-6 months (e.g. Gulu maize
  2021-06 recorded at 2 UGX/kg between 1,222 and 1,086).
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/wfp_food_prices_uga.csv"
OUT = ROOT / "data/processed/monthly.csv"

CROP_OF = {"Maize (white)": "maize", "Maize": "maize", "Beans": "beans"}
# lower = preferred when two commodities map to the same crop in the same month
PRIORITY = {"Maize (white)": 0, "Maize": 1, "Beans": 0}
OUTLIER_FACTOR = 3.0


def load(path: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(path)
    # HDX files sometimes carry an HXL tag row (#date, #adm1+name, ...)
    df = df[~df["date"].astype(str).str.startswith("#")]
    df["price"] = pd.to_numeric(df["price"])
    df["latitude"] = pd.to_numeric(df["latitude"])
    df["longitude"] = pd.to_numeric(df["longitude"])
    return df


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    keep = (
        df["commodity"].isin(CROP_OF)
        & (df["pricetype"] == "Retail")
        & (df["unit"] == "KG")
        & (df["currency"] == "UGX")
        & ~df["market"].str.contains("refugee settlement", case=False)
    )
    d = df[keep].copy()
    d["crop"] = d["commodity"].map(CROP_OF)
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M").dt.to_timestamp()
    d["_prio"] = d["commodity"].map(PRIORITY)
    d = (
        d.sort_values(["crop", "market", "month", "_prio"])
        .drop_duplicates(["crop", "market", "month"], keep="first")
        .rename(columns={"latitude": "lat", "longitude": "lon"})
    )
    cols = ["month", "crop", "market", "admin1", "lat", "lon", "price", "commodity"]
    d = d[cols].sort_values(["crop", "market", "month"]).reset_index(drop=True)
    return d[~entry_errors(d)].reset_index(drop=True)


def entry_errors(d: pd.DataFrame) -> pd.Series:
    """True where a price is > OUTLIER_FACTOR x off its series' neighbours (+-6 months)."""
    bad = pd.Series(False, index=d.index)
    for _, s in d.groupby(["crop", "market"]):
        t = s.month.dt.year.to_numpy() * 12 + s.month.dt.month.to_numpy()
        lp = np.log(s.price.to_numpy())
        for i in range(len(s)):
            near = (np.abs(t - t[i]) <= 6) & (np.arange(len(s)) != i)
            if near.sum() >= 2 and abs(lp[i] - np.median(lp[near])) > np.log(OUTLIER_FACTOR):
                bad[s.index[i]] = True
    return bad


def main() -> None:
    d = tidy(load())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False, date_format="%Y-%m-%d")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d)} rows, {d.market.nunique()} markets")
    print(d.groupby("crop").agg(rows=("price", "size"), markets=("market", "nunique"),
                                first=("month", "min"), last=("month", "max")).to_string())


if __name__ == "__main__":
    main()
