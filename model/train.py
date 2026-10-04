"""Quantile band model: monthly retail price band per (crop, market).

Input:  data/processed/monthly.csv (model/prepare.py)
Output: models/bands.json   contract in docs/BUILD_PLAN.md
        models/metrics.json backtest vs baselines
        models/band_q{10,50,90}.txt  LightGBM boosters (deployment model)

Formulation. From a market's last observed month L we forecast the log price at
T = L + g, g = 1..G_MAX months. The target is the log ratio log(P_T / P_L), so the
baseline "last observed price" is the point y = 0. One LightGBM model per quantile
(0.1, 0.5, 0.9) with g as a feature. g matters because WFP town series stop in
Apr 2026 (Dec 2025 for many markets) while farmers sell today: the band for the
current month is a g = 6..12 month forecast and should widen accordingly.

Features use only data observed at or before L (plus calendar month of T):
own lags 1/2/3/12, last-year change over the same calendar window (L-12 -> T-12,
L-24 -> T-24), deviation from own 24-month mean, premium over the national mean,
national momentum, month of L and T, g, crop, market.

Calibration (per gap g), fitted on rolling-origin out-of-sample predictions
(for each year Y: train on T < Y, predict T in Y):
  - median shrinkage toward the last observed price (lambda_g in [0, 1]), because
    at short gaps the last price is hard to beat;
  - split-conformal widening of [q10, q90] (CQR) so ~80% of OOS targets fall inside;
    raw quantile GBM bands are too narrow in every year we tested.

Backtest: model trained on T <= 2024-12, calibrated on OOS years 2014..2024,
tested on T in 2025-01..2026-04. Robustness: the same for each year 2018..2025
using only prior years. Deployment: trained on all data, calibrated on all OOS years.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MONTHLY = ROOT / "data/processed/monthly.csv"
MODELS = ROOT / "models"

QUANTILES = (0.1, 0.5, 0.9)
G_MAX = 12
CROPS = ["maize", "beans"]
GAP_BUCKETS = {"g1": [1], "g2": [2], "g3": [3], "g4-6": [4, 5, 6], "g7-12": list(range(7, 13))}
YEAR_BUCKETS = {"g1-3": [1, 2, 3], "g4-6": [4, 5, 6], "g7-12": list(range(7, 13))}
FEATURES = ["crop", "market", "g", "m_T", "m_L", "r1", "r2", "r3", "r12",
            "seas12", "seas24", "dev24", "prem", "nat_r1", "nat_r3"]
# num_leaves/min_child_samples picked on the 2024 validation year (fit on T <= 2023)
PARAMS = dict(objective="quantile", n_estimators=300, learning_rate=0.03, num_leaves=7,
              min_child_samples=100, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
              reg_lambda=1.0, verbose=-1, random_state=0)

# backtest windows (month index = year*12 + month-1)
mi = lambda y, m: y * 12 + m - 1  # noqa: E731
TRAIN_END, TEST_START, TEST_END = mi(2024, 12), mi(2025, 1), mi(2026, 4)
OOS_YEARS = range(2014, 2027)


class Panel:
    """Wide log-price panel with padded month index for cheap lookups."""

    def __init__(self, d: pd.DataFrame):
        d = d.copy()
        d["t"] = d.month.dt.year * 12 + d.month.dt.month - 1
        d["lp"] = np.log(d.price)
        self.d = d
        self.sids = sorted(d.groupby(["crop", "market"]).groups)
        self.sid_of = {s: i for i, s in enumerate(self.sids)}
        self.t0 = int(d.t.min()) - 30
        self.t1 = int(d.t.max()) + G_MAX + 30
        idx = range(self.t0, self.t1 + 1)
        wide = d.pivot_table(index="t", columns=["crop", "market"], values="lp")
        wide = wide.reindex(index=idx, columns=pd.MultiIndex.from_tuples(self.sids))
        self.lp = wide.to_numpy()
        self.mean24 = wide.rolling(24, min_periods=6).mean().to_numpy()
        # national aggregates per crop: cross-sectional mean and matched-pair momentum
        self.nat, self.nat_r1, self.nat_r3 = {}, {}, {}
        for c in CROPS:
            w = wide.xs(c, axis=1, level=0)
            n = w.notna().sum(axis=1)
            self.nat[c] = w.mean(axis=1).where(n >= 3).to_numpy()
            for k, store in ((1, self.nat_r1), (3, self.nat_r3)):
                diff = w - w.shift(k)
                store[c] = diff.mean(axis=1).where(diff.notna().sum(axis=1) >= 3).to_numpy()

    def at(self, arr, col, t):
        i = np.asarray(t) - self.t0
        out = np.full(len(i), np.nan)
        ok = (i >= 0) & (i < arr.shape[0])
        out[ok] = arr[i[ok], np.asarray(col)[ok]]
        return out

    def features(self, col, L, g) -> pd.DataFrame:
        col, L, g = np.asarray(col), np.asarray(L), np.asarray(g)
        T = L + g
        lp = lambda t: self.at(self.lp, col, t)  # noqa: E731
        lpL = lp(L)
        crop = np.array([self.sids[c][0] for c in col])
        market = np.array([self.sids[c][1] for c in col])
        nat = np.full(len(col), np.nan)
        nr1, nr3 = nat.copy(), nat.copy()
        for c in CROPS:
            m = crop == c
            i = L[m] - self.t0
            nat[m], nr1[m], nr3[m] = self.nat[c][i], self.nat_r1[c][i], self.nat_r3[c][i]
        # T-12 and T-24 are only usable if they are not after L
        lpT12 = np.where(g <= 12, lp(T - 12), np.nan)
        lpT24 = np.where(g <= 24, lp(T - 24), np.nan)
        return pd.DataFrame({
            "crop": pd.Categorical(crop, categories=CROPS),
            "market": pd.Categorical(market, categories=sorted({s[1] for s in self.sids})),
            "g": g, "m_T": T % 12 + 1, "m_L": L % 12 + 1,
            "r1": lpL - lp(L - 1), "r2": lpL - lp(L - 2), "r3": lpL - lp(L - 3),
            "r12": lpL - lp(L - 12),
            "seas12": lpT12 - lp(L - 12), "seas24": lpT24 - lp(L - 24),
            "dev24": lpL - self.at(self.mean24, col, L),
            "prem": lpL - nat, "nat_r1": nr1, "nat_r3": nr3,
            "_lpL": lpL, "_L": L, "_T": T, "_col": col,
        })

    def training_rows(self) -> pd.DataFrame:
        """All (L, T=L+g) pairs where both months are observed for the same series."""
        obs = self.d.assign(col=[self.sid_of[(c, m)] for c, m in zip(self.d.crop, self.d.market)])
        parts = []
        for g in range(1, G_MAX + 1):
            f = self.features(obs.col.to_numpy(), obs.t.to_numpy(), np.full(len(obs), g))
            f["y"] = self.at(self.lp, f._col.to_numpy(), f._T.to_numpy()) - f._lpL
            parts.append(f[f.y.notna()])
        return pd.concat(parts, ignore_index=True)


def fit(rows: pd.DataFrame) -> dict:
    return {q: lgb.LGBMRegressor(alpha=q, **PARAMS).fit(rows[FEATURES], rows.y) for q in QUANTILES}


def predict(models: dict, rows: pd.DataFrame) -> np.ndarray:
    """(n, 3) log-ratio quantiles, sorted to remove crossing."""
    p = np.column_stack([models[q].predict(rows[FEATURES]) for q in QUANTILES])
    return np.sort(p, axis=1)


def bucket_of(g: np.ndarray, buckets: dict) -> np.ndarray:
    out = np.empty(len(g), dtype=object)
    for name, gs in buckets.items():
        out[np.isin(g, gs)] = name
    return out


def oos_predictions(rows: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Rolling origin: for each year Y, fit on targets T < Y and predict targets in Y."""
    parts, preds = [], []
    for year in OOS_YEARS:
        test = rows[(rows._T >= mi(year, 1)) & (rows._T <= mi(year, 12))]
        if len(test):
            parts.append(test.assign(year=year))
            preds.append(predict(fit(rows[rows._T < mi(year, 1)]), test))
    return pd.concat(parts, ignore_index=True), np.vstack(preds)


def calibrate(rows: pd.DataFrame, pred: np.ndarray, alpha: float = 0.2) -> dict:
    """Per gap g: median shrink toward last price (min abs error) and CQR band widening."""
    y, g = rows.y.to_numpy(), rows.g.to_numpy()
    grid = np.linspace(0, 1, 11)
    out = {}
    for gi in range(1, G_MAX + 1):
        m = g == gi
        lam = grid[np.argmin([np.abs(y[m] - lam * pred[m, 1]).mean() for lam in grid])]
        e = np.maximum(pred[m, 0] - y[m], y[m] - pred[m, 2])
        level = min(1.0, (1 - alpha) * (1 + 1 / m.sum()))
        out[gi] = {"shrink": round(float(lam), 2), "widen": round(float(np.quantile(e, level)), 4)}
    return out


def apply_calibration(pred: np.ndarray, g: np.ndarray, cal: dict) -> np.ndarray:
    g = np.clip(g, 1, G_MAX)
    lam = np.array([cal[x]["shrink"] for x in g])
    w = np.array([cal[x]["widen"] for x in g])
    out = np.column_stack([pred[:, 0] - w, lam * pred[:, 1], pred[:, 2] + w])
    out[:, 0] = np.minimum(out[:, 0], out[:, 1])
    out[:, 2] = np.maximum(out[:, 2], out[:, 1])
    return out


def empirical_band(train: pd.DataFrame, rows: pd.DataFrame) -> np.ndarray:
    """No-ML baseline: last price x historical quantiles of the g-month change, per crop."""
    qs = train.groupby(["crop", "g"], observed=True).y.quantile(list(QUANTILES)).unstack()
    key = pd.MultiIndex.from_arrays([rows.crop.astype(str), rows.g])
    return qs.reindex(key).to_numpy()


def score(rows: pd.DataFrame, pred: np.ndarray) -> dict:
    """Metrics in price space (UGX/kg). pred holds log-ratio quantiles."""
    pL = np.exp(rows._lpL.to_numpy())
    y = pL * np.exp(rows.y.to_numpy())
    p10, p50, p90 = (pL * np.exp(pred[:, i]) for i in range(3))
    ae, ae_base = np.abs(p50 - y), np.abs(pL - y)

    def pinball(q, pr):
        d = rows.y.to_numpy() - pr
        return np.maximum(q * d, (q - 1) * d)

    return {
        "n": int(len(rows)),
        "coverage_p10_p90": round(float(np.mean((y >= p10) & (y <= p90))), 3),
        "median_rel_width": round(float(np.median((p90 - p10) / p50)), 3),
        "mae_p50_ugx": round(float(ae.mean()), 1),
        "mae_last_obs_ugx": round(float(ae_base.mean()), 1),
        "mae_skill_vs_last_obs": round(float(1 - ae.mean() / ae_base.mean()), 3),
        "mape_p50": round(float(np.mean(ae / y)), 3),
        "mape_last_obs": round(float(np.mean(ae_base / y)), 3),
        "pinball_log": round(float(np.mean([pinball(q, pred[:, i]).mean()
                                            for i, q in enumerate(QUANTILES)])), 4),
    }


def score_groups(rows: pd.DataFrame, pred: np.ndarray) -> dict:
    out = {"all": score(rows, pred)}
    gb = bucket_of(rows.g.to_numpy(), GAP_BUCKETS)
    for name in GAP_BUCKETS:
        m = gb == name
        out[name] = score(rows[m], pred[m])
    for c in CROPS:
        for name in ("g1", "g7-12"):
            m = (rows.crop == c).to_numpy() & (gb == name)
            out[f"{c}_{name}"] = score(rows[m], pred[m])
    return out


def backtest(rows: pd.DataFrame, oos_rows: pd.DataFrame, oos_pred: np.ndarray):
    train = rows[rows._T <= TRAIN_END]
    test = rows[(rows._T >= TEST_START) & (rows._T <= TEST_END)].reset_index(drop=True)
    prior = (oos_rows.year <= 2024).to_numpy()
    cal = calibrate(oos_rows[prior], oos_pred[prior])
    raw = predict(fit(train), test)
    res = {
        "model_calibrated": score_groups(test, apply_calibration(raw, test.g.to_numpy(), cal)),
        "model_raw": score_groups(test, raw),
        "empirical_band_no_ml": score_groups(test, empirical_band(train, test)),
    }
    # robustness: every year scored with model and calibration fitted on prior years only
    by_year = []
    for year in range(2018, 2026):
        prior, cur = (oos_rows.year < year).to_numpy(), (oos_rows.year == year).to_numpy()
        te = oos_rows[cur]
        pm = apply_calibration(oos_pred[cur], te.g.to_numpy(),
                               calibrate(oos_rows[prior], oos_pred[prior]))
        pe = empirical_band(rows[rows._T < mi(year, 1)], te)
        gb = bucket_of(te.g.to_numpy(), YEAR_BUCKETS)
        for b in YEAR_BUCKETS:
            m = gb == b
            sm, se = score(te[m], pm[m]), score(te[m], pe[m])
            by_year.append({"year": year, "gap": b, "n": sm["n"],
                            "coverage_model": sm["coverage_p10_p90"],
                            "coverage_empirical": se["coverage_p10_p90"],
                            "mae_skill_model": sm["mae_skill_vs_last_obs"],
                            "mae_skill_empirical": se["mae_skill_vs_last_obs"],
                            "pinball_model": sm["pinball_log"],
                            "pinball_empirical": se["pinball_log"]})
    return res, cal, by_year


def market_meta(p: Panel) -> dict:
    meta = p.d.sort_values("month").groupby("market").last()
    out = {}
    for m, r in meta.iterrows():
        key = m.lower()
        aliases = [key] + ([key.replace(" ", "")] if " " in key else [])
        if m == "Owino":
            aliases += ["kampala", "st balikuddembe"]
        out[m] = {"aliases": aliases, "admin1": r.admin1,
                  "lat": round(float(r.lat), 2), "lon": round(float(r.lon), 2)}
    return out


def r10(x: float) -> int:
    return int(round(x / 10.0) * 10)


def make_bands(p: Panel, models: dict, cal: dict, asof: pd.Timestamp,
               max_age_months: int) -> dict:
    t_now = asof.year * 12 + asof.month - 1
    last = p.d.sort_values("t").groupby(["crop", "market"]).last()
    last = last[last.t >= t_now - max_age_months]
    cols = np.array([p.sid_of[s] for s in last.index])
    L = last.t.to_numpy()
    bands = {}
    per_h = []
    for h in (1, 2, 3):
        g_true = t_now + h - 1 - L
        g = np.clip(g_true, 1, G_MAX)  # beyond G_MAX: reuse the widest trained gap
        f = p.features(cols, L, g)
        # keep the real calendar month of the target even when g is clipped
        f["m_T"] = (t_now + h - 1) % 12 + 1
        pred = apply_calibration(predict(models, f), g, cal)
        per_h.append((g_true, np.exp(f._lpL.to_numpy())[:, None] * np.exp(pred)))
    for i, (crop, market) in enumerate(last.index):
        r = last.loc[(crop, market)]
        b = {"last_obs_date": (r.month + pd.Timedelta(days=14)).strftime("%Y-%m-%d"),
             "last_obs_price": r10(r.price)}
        for h, (g_true, pr) in enumerate(per_h, start=1):
            b[f"h{h}"] = {"p10": r10(pr[i, 0]), "p50": r10(pr[i, 1]), "p90": r10(pr[i, 2])}
        b["n_reports"] = 0
        b["gap_months_h1"] = int(per_h[0][0][i])
        bands[f"{crop}|{market}"] = b
    return bands


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", help="reference month YYYY-MM for h1 (default: today)")
    ap.add_argument("--max-age-months", type=int, default=24,
                    help="drop series whose last observation is older than this")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    asof = pd.Timestamp(args.asof + "-01") if args.asof else pd.Timestamp(now.year, now.month, 1)

    d = pd.read_csv(MONTHLY, parse_dates=["month"])
    p = Panel(d)
    rows = p.training_rows()
    print(f"training rows (all L,g pairs): {len(rows)}")

    oos_rows, oos_pred = oos_predictions(rows)
    results, cal_backtest, by_year = backtest(rows, oos_rows, oos_pred)
    cols = ["n", "coverage_p10_p90", "median_rel_width", "mae_p50_ugx", "mae_last_obs_ugx",
            "mae_skill_vs_last_obs", "pinball_log"]
    for name, res in results.items():
        print(f"\n== test 2025-01..2026-04: {name}")
        print(pd.DataFrame(res).T[cols].to_string())
    yr = pd.DataFrame(by_year)
    print("\n== robustness 2018..2025 (prior-years-only fit + calibration)")
    print(yr.to_string(index=False))
    print(yr.drop(columns=["year", "n"]).groupby("gap").mean().round(3).to_string())

    # deployment model: all data; calibration from all out-of-sample years
    cal = calibrate(oos_rows, oos_pred)
    models = fit(rows)
    MODELS.mkdir(exist_ok=True)
    sizes = {}
    for q, m in models.items():
        path = MODELS / f"band_q{int(q * 100)}.txt"
        m.booster_.save_model(str(path))
        sizes[path.name] = path.stat().st_size

    bands = make_bands(p, models, cal, asof, args.max_age_months)
    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reference_month": asof.strftime("%Y-%m"),
        "currency": "UGX", "unit": "KG", "price_type": "retail",
        "source": "WFP Food Prices Uganda via HDX (CC BY-IGO); town markets, retail",
        "markets": {m: v for m, v in market_meta(p).items()
                    if any(k.endswith("|" + m) for k in bands)},
        "bands": bands,
    }
    (MODELS / "bands.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

    metrics = {
        "generated_at": out["generated_at"],
        "data": {"rows_monthly": int(len(d)), "series": len(p.sids),
                 "markets": int(d.market.nunique()),
                 "first_month": d.month.min().strftime("%Y-%m"),
                 "last_month": d.month.max().strftime("%Y-%m")},
        "setup": {"target": "log(P_T / P_L), T = L + g, g = 1..12 months after last obs",
                  "quantiles": list(QUANTILES), "features": FEATURES, "params": PARAMS,
                  "calibration": "rolling-origin OOS years 2014..2024 (backtest), "
                                 "2014..2026 (deployment); per gap: median shrink + CQR",
                  "train_for_test": "T <= 2024-12", "test": "T in 2025-01..2026-04",
                  "baseline_point": "last observed price P_L",
                  "baseline_band": "P_L x empirical quantiles of g-month change per crop (no ML)",
                  "n_training_rows_all": int(len(rows))},
        "calibration_backtest": cal_backtest,
        "calibration_deploy": cal,
        "backtest": results,
        "robustness_by_year": by_year,
        "model_files_bytes": sizes,
        "bands_json_bytes": (MODELS / "bands.json").stat().st_size,
        "n_bands": len(bands),
    }
    (MODELS / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    print(f"\nwrote models/bands.json ({len(bands)} bands, ref month {out['reference_month']}), "
          f"models/metrics.json, model files {sizes}")


if __name__ == "__main__":
    main()
