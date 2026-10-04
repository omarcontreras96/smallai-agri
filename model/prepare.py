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
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/wfp_food_prices_uga.csv"
OUT = ROOT / "data/processed/monthly.csv"

CROP_OF = {"Maize (white)": "maize", "Maize": "maize", "Beans": "beans"}
# lower = preferred when two commodities map to the same crop in the same month
PRIORITY = {"Maize (white)": 0, "Maize": 1, "Beans": 0}


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
    return d[cols].sort_values(["crop", "market", "month"]).reset_index(drop=True)


def main() -> None:
    d = tidy(load())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False, date_format="%Y-%m-%d")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d)} rows, {d.market.nunique()} markets")
    print(d.groupby("crop").agg(rows=("price", "size"), markets=("market", "nunique"),
                                first=("month", "min"), last=("month", "max")).to_string())


if __name__ == "__main__":
    main()
