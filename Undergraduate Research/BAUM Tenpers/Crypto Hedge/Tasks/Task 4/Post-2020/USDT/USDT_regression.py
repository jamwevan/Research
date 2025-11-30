#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USDT regressions FROM PRICE LEVELS, applying transforms dictated by the () suffix.

Rules:
  "(Natural Log Changes)" -> Δlog(level)  [decimals]
  "(Changes)"              -> Δlevel

This script NEVER uses pre-transformed data. It treats the columns in your
workbook as LEVEL series. If a sheet’s headers already include the suffix
(e.g., "SPXT Index (Natural Log Changes)"), we still treat that column as the LEVEL
series and then apply the specified transform to it.

Output:
  USDT_regressions.tex   (LaTeX table per sheet, stepwise specs)
"""

import re
import difflib
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ========================== CONFIG ==========================
FILE = "program_data.xlsx"   # Workbook with LEVEL columns + Date
DATE_COL = "Date"            # Optional date column for sorting

# If you want to enforce a time window, set START_DATE / END_DATE (or leave None)
START_DATE = None            # e.g., "2020-01-01"
END_DATE   = None            # e.g., "2025-10-01"

# Optional manual overrides (rare). Left: desired LEVEL name (no suffix),
# Right: actual column name in the sheet.
OVERRIDES = {
    # "SPXT Index": "SPXT Index",             # example
    # "USTWBGD  Index": "USTWBGD  Index",     # example (double space kept)
}

# Regression specs (NAMES WITH SUFFIXES tell us which transform to apply)
regression_specs = {
    "US Regression": {
        "dependent": "SPXT Index (Natural Log Changes)",
        "independents": [
            "USDT_USD (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)"
        ]
    },
    "UK Regression": {
        "dependent": "UKX Index (Natural Log Changes)",
        "independents": [
            "USDT_GBP (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTGBPII10YR @BGN Corp (Changes)",
            "GTGBP3MO @BGN Corp (Changes)"
        ]
    },
    "Eurozone Regression": {
        "dependent": "SXXP Index (Natural Log Changes)",
        "independents": [
            "USDT_EUR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTEUR10YR @BGN Corp (Changes)",
            "GTEUR3MO @BGN Corp (Changes)"
        ]
    },
    "Japan Regression": {
        "dependent": "NKYTR Index (Natural Log Changes)",
        "independents": [
            "USDT_JPY (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTJPY10YR @BGN Corp (Changes)",
            "GTJPY3MO @BGN Corp (Changes)"
        ]
    },
    "China Regression": {
        "dependent": "SHCOMP Index (Natural Log Changes)",
        "independents": [
            "USDT_CNY (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTCNY10YR @CHBE Corp (Changes)",
            "GTCNY1YR @CHBE Corp (Changes)"
        ]
    },
    "Brazil Regression": {
        "dependent": "IBOV Index (Natural Log Changes)",
        "independents": [
            "USDT_BRL (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTBRL10YR @BGN Corp (Changes)",
            "GTBRL1YR @BGN Corp (Changes)"
        ]
    },
    "India Regression": {
        "dependent": "NIFTY Index (Natural Log Changes)",
        "independents": [
            "USDT_INR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTINR10YR @NDSI Corp (Changes)",
            "GTINR2YR @NDSI Corp (Changes)"
        ]
    },
    "South Africa Regression": {
        "dependent": "JALSH Index (Natural Log Changes)",
        "independents": [
            "USDT_ZAR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTZAR10YR @BGN Corp (Changes)",
            "GTZAR1YR @BGN Corp (Changes)"
        ]
    }
}

# Pretty labels for LaTeX rows
label_map = {
    "USDT_USD (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{USD})$",
    "USDT_GBP (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{GBP})$",
    "USDT_EUR (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{EUR})$",
    "USDT_JPY (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{JPY})$",
    "USDT_CNY (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{CNY})$",
    "USDT_BRL (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{BRL})$",
    "USDT_INR (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{INR})$",
    "USDT_ZAR (Natural Log Changes)":  r"$\Delta \log(\mathrm{USDT}_{ZAR})$",
    "BCOM Index (Changes)":            r"$\Delta \mathrm{Commodity}$",
    "USTWBGD  Index (Changes)":        r"$\Delta \mathrm{Dollar}$",
    "VIX Index (Changes)":             r"$\Delta \mathrm{VIX}$",
    "USGG10YR Index (Changes)":        r"$\Delta \mathrm{10Y\ Yield}$",
    "USGG1M Index (Changes)":          r"$\Delta \mathrm{1M\ Yield}$",
    "GTBRL10YR @BGN Corp (Changes)":   r"$\Delta \mathrm{10Y\ Spread}$",
    "GTBRL1YR @BGN Corp (Changes)":    r"$\Delta \mathrm{1Y\ Spread}$",
    "GTGBPII10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTGBP3MO @BGN Corp (Changes)":    r"$\Delta \mathrm{3M\ Spread}$",
    "GTEUR10YR @BGN Corp (Changes)":   r"$\Delta \mathrm{10Y\ Spread}$",
    "GTEUR3MO @BGN Corp (Changes)":    r"$\Delta \mathrm{3M\ Spread}$",
    "GTJPY10YR @BGN Corp (Changes)":   r"$\Delta \mathrm{10Y\ Spread}$",
    "GTJPY3MO @BGN Corp (Changes)":    r"$\Delta \mathrm{3M\ Spread}$",
    "GTCNY10YR @CHBE Corp (Changes)":  r"$\Delta \mathrm{10Y\ Spread}$",
    "GTCNY1YR @CHBE Corp (Changes)":   r"$\Delta \mathrm{1Y\ Spread}$",
    "GTINR10YR @NDSI Corp (Changes)":  r"$\Delta \mathrm{10Y\ Spread}$",
    "GTINR2YR @NDSI Corp (Changes)":   r"$\Delta \mathrm{2Y\ Spread}$",
    "GTZAR10YR @BGN Corp (Changes)":   r"$\Delta \mathrm{10Y\ Spread}$",
    "GTZAR1YR @BGN Corp (Changes)":    r"$\Delta \mathrm{1Y\ Spread}$",
}
# ======================== END CONFIG ========================


# ---------- Name cleaning & resolution ----------
_space_re = re.compile(r"\s+")

def clean_name(s: str) -> str:
    """
    Lowercase, strip, collapse spaces. Also keep vendor suffixes in place; we
    accept them as-is since your sheets may use the suffixed header as the LEVEL name.
    """
    s = str(s).replace("\u00A0", " ")
    s = _space_re.sub(" ", s.strip())
    return s.lower()

def level_name(name_with_suffix: str) -> str:
    """Strip the () suffix to get the intended human-level name."""
    return (name_with_suffix
            .replace(" (Natural Log Changes)", "")
            .replace(" (Changes)", ""))

def build_lookup(df: pd.DataFrame) -> dict:
    """Map cleaned header -> original header."""
    return {clean_name(c): c for c in df.columns}

def resolve_level_col(df: pd.DataFrame, desired_level_name: str, original_with_suffix: str) -> str:
    """
    Resolve which COLUMN in df to treat as the LEVEL series for 'desired_level_name'.

    Priority:
      1) Exact/normalized match to the base name (no suffix)
      2) Fallback: the suffixed header itself (your workbook uses these as LEVEL headers)
      3) Fuzzy match (>=0.85) of the base name
    """
    lut = build_lookup(df)

    # 1) Try base (no suffix)
    base_key = clean_name(desired_level_name)
    if base_key in lut:
        return lut[base_key]

    # 2) Fallback to the suffixed header itself
    suff_key = clean_name(original_with_suffix)
    if suff_key in lut:
        return lut[suff_key]

    # 3) Fuzzy last resort against actual headers
    best = difflib.get_close_matches(desired_level_name, list(df.columns), n=1, cutoff=0.85)
    if best:
        print(f"[warn] Fuzzy-matched '{desired_level_name}' -> '{best[0]}'")
        return best[0]

    raise KeyError(
        f"Missing LEVEL column for '{desired_level_name}'. "
        f"Available columns: {', '.join(map(str, df.columns))}"
    )

def build_series_from_levels(df: pd.DataFrame, name_with_suffix: str) -> pd.Series:
    """
    Apply the transform indicated by the suffix to the resolved LEVEL column.

    '(Natural Log Changes)' -> Δlog(level)  [decimals]
    '(Changes)'             -> Δlevel
    """
    base = level_name(name_with_suffix)
    lvl_col = resolve_level_col(df, base, name_with_suffix)
    s = pd.to_numeric(df[lvl_col], errors="coerce")

    if name_with_suffix.endswith("(Natural Log Changes)"):
        return np.log(s).diff()
    elif name_with_suffix.endswith("(Changes)"):
        return s.diff()
    else:
        raise ValueError(f"Unknown transform suffix in '{name_with_suffix}'")

def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


# ------------------------------ MAIN ------------------------------
def run_sheet(sheet_name: str, spec: dict, writer):
    df = pd.read_excel(FILE, sheet_name=sheet_name)

    # Date handling (optional)
    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
        df = df.sort_values(DATE_COL)
        if START_DATE is not None:
            df = df[df[DATE_COL] >= pd.Timestamp(START_DATE)]
        if END_DATE is not None:
            df = df[df[DATE_COL] <= pd.Timestamp(END_DATE)]
    df = df.reset_index(drop=True)

    # Build FROM LEVELS
    y_full = build_series_from_levels(df, spec["dependent"]).rename(spec["dependent"])
    X_all = {nm: build_series_from_levels(df, nm) for nm in spec["independents"]}
    X_all = pd.DataFrame(X_all)

    # Stepwise models (add controls one-by-one)
    models = []
    order = spec["independents"]
    for i in range(1, len(order) + 1):
        T = pd.concat([y_full, X_all[order[:i]]], axis=1).dropna()
        if T.shape[0] < 20:
            raise ValueError(f"Too few rows after transforms in '{sheet_name}' (step {i}); got {T.shape[0]}")
        X = sm.add_constant(T[order[:i]], has_constant="add")
        m = sm.OLS(T[spec["dependent"]], X).fit()
        models.append(m)

    # LaTeX table
    lines = []
    lines.append("\\begin{table}[H]")
    lines.append("\\centering")
    lines.append(f"\\caption{{Tether {sheet_name}}}")
    lines.append("\\resizebox{\\textwidth}{!}{%")
    lines.append("\\begin{tabular}{l" + "c" * len(models) + "}")
    lines.append("\\toprule")
    lines.append(f" & {' & '.join([f'({i+1})' for i in range(len(models))])} \\\\")
    lines.append("\\midrule")

    for var in order:
        lab = label_map.get(var, var)
        coefs, ses = [], []
        for m in models:
            if var in m.params.index:
                coef, se, p = m.params[var], m.bse[var], m.pvalues[var]
                coefs.append(f"{coef:.3f}{stars(p)}")
                ses.append(f"({se:.3f})")
            else:
                coefs.append("")
                ses.append("")
        lines.append(f"{lab} & " + " & ".join(coefs) + " \\\\")
        lines.append(" & " + " & ".join(ses) + " \\\\")

    lines.append("\\midrule")
    lines.append("Observations & " + " & ".join([f"{int(m.nobs)}" for m in models]) + " \\\\")
    lines.append("Adj. $R^2$ & " + " & ".join([f"{m.rsquared_adj:.3f}" for m in models]) + " \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("}")  # close resizebox
    lines.append("\\begin{tablenotes}")
    lines.append("\\footnotesize")
    lines.append("Note: Dependent variable shown in caption. SE in parentheses. "
                 "*** p$<$0.01, ** p$<$0.05, * p$<$0.1.")
    lines.append("\\end{tablenotes}")
    lines.append("\\end{table}\n")

    writer.write("\n".join(lines) + "\n\n")


if __name__ == "__main__":
    with open("USDT_regressions.tex", "w") as f_out:
        for sheet, spec in regression_specs.items():
            run_sheet(sheet, spec, f_out)
    print("All USDT regressions completed FROM LEVELS. Results saved to USDT_regressions.tex")
