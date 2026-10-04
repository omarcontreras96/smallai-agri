"""Backtest chart for the slides: error and band coverage by months since last price.

Evaluation = the robustness setup in train.py: for each year 2018..2025, model and
calibration fitted only on earlier years; all (market, month, gap) cases pooled.

Output: docs/slides/backtest.png (chart), docs/slides/backtest.csv (table view)
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train as T  # noqa: E402

OUT = T.ROOT / "docs/slides"
YEARS = range(2018, 2026)

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
MODEL, SHEET, LAST = "#2a78d6", "#eb6834", MUTED


def evaluate() -> pd.DataFrame:
    d = pd.read_csv(T.MONTHLY, parse_dates=["month"])
    p = T.Panel(d)
    rows = p.training_rows()
    oos_rows, oos_pred = T.oos_predictions(rows)
    parts = []
    for year in YEARS:
        prior, cur = (oos_rows.year < year).to_numpy(), (oos_rows.year == year).to_numpy()
        te = oos_rows[cur]
        y = te.y.to_numpy()
        pm = T.apply_calibration(oos_pred[cur], te.g.to_numpy(),
                                 T.calibrate(oos_rows[prior], oos_pred[prior]))
        pe = T.empirical_band(rows[rows._T < T.mi(year, 1)], te)
        parts.append(pd.DataFrame({
            "g": te.g.to_numpy(),
            # |P50 - P_T| / P_T with P50 = P_L e^m and P_T = P_L e^y
            "err_model": np.abs(np.exp(pm[:, 1] - y) - 1),
            "err_last": np.abs(np.exp(-y) - 1),
            "cov_model": (pm[:, 0] <= y) & (y <= pm[:, 2]),
            "cov_sheet": (pe[:, 0] <= y) & (y <= pe[:, 2]),
        }))
    out = pd.concat(parts).groupby("g").agg(
        n=("err_model", "size"), err_model=("err_model", "mean"), err_last=("err_last", "mean"),
        cov_model=("cov_model", "mean"), cov_sheet=("cov_sheet", "mean"))
    return out.reset_index()


def style(ax, ylabel_fmt):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelcolor=INK2, length=0, labelsize=11)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(ylabel_fmt))
    ax.set_xticks(range(1, 13))
    ax.set_xlim(0.6, 12.4)
    ax.set_xlabel("Months since the market's last published price", color=INK2, fontsize=11,
                  labelpad=8)


def line(ax, x, y, color, label):
    ax.plot(x, y, color=color, linewidth=2.2, solid_capstyle="round", solid_joinstyle="round",
            marker="o", markersize=7, markerfacecolor=color, markeredgecolor=SURFACE,
            markeredgewidth=1.6, label=label, zorder=3)


def end_label(ax, x, y, text, dy=0):
    ax.annotate(text, (x, y), xytext=(8, dy), textcoords="offset points", va="center",
                fontsize=11, color=INK, fontweight="semibold")


def plot(s: pd.DataFrame) -> Path:
    plt.rcParams["font.family"] = ["Helvetica Neue", "Arial", "DejaVu Sans"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.8, 7.2), dpi=125)
    fig.patch.set_facecolor(SURFACE)
    pct = lambda v, _: f"{v:.0%}"  # noqa: E731
    g = s.g.to_numpy()

    style(a, pct)
    line(a, g, s.err_last, LAST, "Last published price")
    line(a, g, s.err_model, MODEL, "Model (median)")
    a.set_ylim(0, max(s.err_last.max(), s.err_model.max()) * 1.18)
    end_label(a, 12, s.err_last.iloc[-1], f"{s.err_last.iloc[-1]:.0%}")
    end_label(a, 12, s.err_model.iloc[-1], f"{s.err_model.iloc[-1]:.0%}")
    a.set_title("Typical error, % of the real price (lower is better)", loc="left",
                color=INK, fontsize=13, fontweight="semibold", pad=34)
    a.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=11,
             labelcolor=INK2, handlelength=1.8, borderaxespad=0.3)

    style(b, pct)
    b.hlines(0.8, 0.6, 12.15, color=INK2, linewidth=1, zorder=2)
    b.annotate("Target 80%", (0.75, 0.8), xytext=(0, -16), textcoords="offset points",
               fontsize=11, color=INK2)
    line(b, g, s.cov_sheet, SHEET, "Spreadsheet band (no AI)")
    line(b, g, s.cov_model, MODEL, "Model band")
    b.set_ylim(0.4, 1.0)
    end_label(b, 12, s.cov_model.iloc[-1], f"{s.cov_model.iloc[-1]:.0%}")
    end_label(b, 12, s.cov_sheet.iloc[-1], f"{s.cov_sheet.iloc[-1]:.0%}")
    b.set_title("Real prices inside the 10–90% band (target 80%)", loc="left",
                color=INK, fontsize=13, fontweight="semibold", pad=34)
    b.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=11,
             labelcolor=INK2, handlelength=1.8, borderaxespad=0.3)

    fig.suptitle("The older the price data, the more the model helps", x=0.055, y=0.965,
                 ha="left", fontsize=20, fontweight="bold", color=INK)
    fig.text(0.055, 0.885,
             f"Uganda maize and beans, 28 town markets, {YEARS[0]}–{YEARS[-1]}. Each year "
             f"predicted using only earlier years; {int(s.n.sum()):,} test cases. "
             "Source: WFP via HDX (CC BY-IGO).",
             ha="left", fontsize=11.5, color=INK2)
    fig.subplots_adjust(left=0.055, right=0.955, top=0.78, bottom=0.11, wspace=0.18)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "backtest.png"
    fig.savefig(path, facecolor=SURFACE)
    return path


def main() -> None:
    s = evaluate()
    s.round(4).to_csv(OUT / "backtest.csv", index=False)
    print(s.round(3).to_string(index=False))
    print(f"wrote {plot(s).relative_to(T.ROOT)}, docs/slides/backtest.csv")


if __name__ == "__main__":
    main()
