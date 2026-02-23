#!/usr/bin/env python3
"""
run_lp.py

Regime-conditional local projections for JPY basis, using the workbook:
    JPY_iwe irf.xlsx

Reads the 'lp_ready' sheet (engineered regressors + basis levels) and produces:
  1) lp_results.csv  (master tidy results by maturity and horizon)
  2) table_lp_{n}y.tex for n in {1,5,10,20,30}
  3) irf_{n}y.pdf plots for n in {1,5,10,20,30}

All outputs are written to the current working directory.

Requires: pandas, numpy, statsmodels, matplotlib, openpyxl
"""

from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


# -------------------------
# Configuration (matches your lp_ready sheet)
# -------------------------
WORKBOOK = "JPY_iwe irf.xlsx"
SHEET = "lp_ready"

MATURITIES = [1, 5, 10, 20, 30]
HORIZONS = list(range(0, 9))  # h = 0..8

KEY_REGRESSORS = ["dD_low", "dD_high"]
CONTROLS = ["dVIX", "dIV", "dRR", "dYS", "dTS"]  # keep exactly these column names
X_COLS = KEY_REGRESSORS + CONTROLS

# Confidence band for plots (90%)
Z_CI = 1.645


def stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt(x: float, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    return f"{x:.{digits}f}"


def require_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(
            "Missing required columns in lp_ready: "
            + ", ".join(missing)
            + "\nCheck the lp_ready sheet headers."
        )


def run_lp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run local projections for each maturity n and horizon h.
    Returns a wide tidy dataframe with columns like beta_low, se_low, beta_high, se_high, etc.
    """
    results = []

    for n in MATURITIES:
        for h in HORIZONS:
            # Build dependent variable internally to avoid Excel blank-as-zero issues.
            # Jordà LP target: y^{(h)}_{n,t} = x_{n,t+h} - x_{n,t-1}
            x_col = f"x{n}"
            require_columns(df, [x_col] + X_COLS)

            y_series = df[x_col].astype(float).shift(-h) - df[x_col].astype(float).shift(1)
            sub = df[X_COLS].copy()
            sub = sub.assign(y=y_series)
            sub = sub.dropna(subset=["y"] + X_COLS)

            y = sub["y"].astype(float)
            X = sub[X_COLS].astype(float)
            X = sm.add_constant(X, has_constant="add")

            # Jordà-style HAC: lag = h + 1
            model = sm.OLS(y, X, missing="drop")
            res = model.fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})

            # Store only the regime coefficients, plus basic stats
            results.append(
                {
                    "maturity": n,
                    "h": h,
                    "beta_low": float(res.params["dD_low"]),
                    "se_low": float(res.bse["dD_low"]),
                    "t_low": float(res.tvalues["dD_low"]),
                    "p_low": float(res.pvalues["dD_low"]),
                    "beta_high": float(res.params["dD_high"]),
                    "se_high": float(res.bse["dD_high"]),
                    "t_high": float(res.tvalues["dD_high"]),
                    "p_high": float(res.pvalues["dD_high"]),
                    "N": int(res.nobs),
                    "r2": float(res.rsquared),
                    "hac_lag": h + 1,
                }
            )

    return pd.DataFrame(results).sort_values(["maturity", "h"]).reset_index(drop=True)


def write_latex_tables(res: pd.DataFrame, outdir: Path) -> None:
    """
    One table per maturity; columns are horizons (0..8), rows are low/high coefficients with HAC SEs.
    """
    for n in MATURITIES:
        sub = res[res["maturity"] == n].sort_values("h")
        # Build columns by horizon
        coef_low = [fmt(b) + stars(p) for b, p in zip(sub["beta_low"], sub["p_low"])]
        se_low = [f"({fmt(s)})" for s in sub["se_low"]]
        coef_high = [fmt(b) + stars(p) for b, p in zip(sub["beta_high"], sub["p_high"])]
        se_high = [f"({fmt(s)})" for s in sub["se_high"]]
        Ns = [str(int(x)) for x in sub["N"]]

        cols = "l" + "c" * len(HORIZONS)
        header = " & " + " & ".join([str(h) for h in HORIZONS]) + r" \\"

        lines = []
        lines.append(r"\begin{table}[!htbp]\centering")
        lines.append(r"\caption{Regime-conditional local projections: JPY basis (" + f"{n}Y" + r")}")
        lines.append(r"\label{tab:lp_jpy_" + f"{n}y" + r"}")
        lines.append(r"\begin{tabular}{" + cols + r"}")
        lines.append(r"\toprule")
        lines.append(r"Horizon $h$" + header)
        lines.append(r"\midrule")
        lines.append(r"$\Delta D_t \times \mathbf{1}\{D_t \le D_\tau\}$" + " & " + " & ".join(coef_low) + r" \\")
        lines.append(r" " + " & " + " & ".join(se_low) + r" \\")
        lines.append(r"$\Delta D_t \times \mathbf{1}\{D_t > D_\tau\}$" + " & " + " & ".join(coef_high) + r" \\")
        lines.append(r" " + " & " + " & ".join(se_high) + r" \\")
        lines.append(r"\midrule")
        lines.append(r"Observations" + " & " + " & ".join(Ns) + r" \\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(
            r"\begin{flushleft}\footnotesize "
            r"Notes: Each column reports the coefficient from a separate local projection at horizon $h=0,\dots,8$. "
            r"Dependent variable is $x_{t+h}-x_{t-1}$ for the "
            + f"{n}Y"
            + r" basis. Regressors include $\Delta D_t$ interacted with dollar regimes, and controls "
            r"($\Delta$VIX, $\Delta$IV, $\Delta$RR, $\Delta$YS, $\Delta$TS). "
            r"Standard errors are Newey--West (HAC) with lag $h+1$. "
            r"$^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.10$."
            r"\end{flushleft}"
        )
        lines.append(r"\end{table}")

        outpath = outdir / f"table_lp_{n}y.tex"
        outpath.write_text("\n".join(lines), encoding="utf-8")


def write_irf_plots(res: pd.DataFrame, outdir: Path) -> None:
    """
    One plot per maturity showing beta_low and beta_high with 90% CI bands.
    """
    for n in MATURITIES:
        sub = res[res["maturity"] == n].sort_values("h")
        h = sub["h"].to_numpy()

        beta_low = sub["beta_low"].to_numpy()
        se_low = sub["se_low"].to_numpy()
        beta_high = sub["beta_high"].to_numpy()
        se_high = sub["se_high"].to_numpy()

        plt.figure()
        plt.plot(h, beta_low, label="Low-dollar regime")
        plt.fill_between(h, beta_low - Z_CI * se_low, beta_low + Z_CI * se_low, alpha=0.2)

        plt.plot(h, beta_high, label="High-dollar regime")
        plt.fill_between(h, beta_high - Z_CI * se_high, beta_high + Z_CI * se_high, alpha=0.2)

        plt.axhline(0, linewidth=1)
        plt.xticks(h)
        plt.xlabel("Horizon h (weeks)")
        plt.ylabel("IRF: coefficient on $\Delta D$")
        plt.title(f"Regime-conditional local projections (JPY basis {n}Y)")
        plt.legend()

        outpath = outdir / f"irf_{n}y.pdf"
        plt.savefig(outpath, bbox_inches="tight")
        plt.close()


def main() -> None:
    here = Path(".").resolve()
    wb = here / WORKBOOK
    if not wb.exists():
        raise FileNotFoundError(f"Could not find workbook: {wb}")

    try:
        df = pd.read_excel(wb, sheet_name=SHEET)
    except ValueError as e:
        # Helpful message if the expected sheet name isn't present
        import openpyxl
        wb_obj = openpyxl.load_workbook(wb, read_only=True)
        sheets = wb_obj.sheetnames
        raise ValueError(
            f"Worksheet named '{SHEET}' not found in {wb.name}. "
            f"Available sheets: {sheets}. "
            "Open the workbook, ensure the tab is named exactly 'lp_ready', save, and rerun."
        ) from e

    # Basic sanity check that the engineered columns exist
    require_columns(df, X_COLS + [f"x{n}" for n in MATURITIES])

    res = run_lp(df)

    # Output 1: master results
    csv_path = here / "lp_results.csv"
    res.to_csv(csv_path, index=False)

    # Output 2: LaTeX tables
    write_latex_tables(res, here)

    # Output 3: IRF plots
    write_irf_plots(res, here)

    print("Done.")
    print(f"Wrote: {csv_path.name}")
    print("Wrote: table_lp_{1,5,10,20,30}y.tex")
    print("Wrote: irf_{1,5,10,20,30}y.pdf")


if __name__ == "__main__":
    main()
