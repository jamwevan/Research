#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XRP regressions FROM PRICE LEVELS, applying transforms dictated by the () suffix.

Rules:
  "(Natural Log Changes)" -> Δlog(level)  [decimals]
  "(Changes)"              -> Δlevel

This script NEVER uses pre-transformed data. Even if a header includes the suffix
(e.g., "SPXT Index (Natural Log Changes)"), we treat that column as the LEVEL series
and then apply the specified transform to it.

Output:
  XRP_regressions.tex  (LaTeX table per sheet, stepwise specs)
"""

import re
import difflib
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ---------- I/O ----------
file = "program_data.xlsx"
xls = pd.ExcelFile(file)
DATE_COL = "Date"           # if present, used to sort/align chronologically
START_DATE = None           # e.g., "2020-01-01" to pin a window; else None
END_DATE   = None

# ---------- Regression specs for all countries (XRP) ----------
regression_specs = {
    "US Regression": {
        "dependent": "SPXT Index (Natural Log Changes)",
        "independents": [
            "XRP_USD (Natural Log Changes)",
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
            "XRP_GBP (Natural Log Changes)",
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
            "XRP_EUR (Natural Log Changes)",
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
            "XRP_JPY (Natural Log Changes)",
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
            "XRP_CNY (Natural Log Changes)",
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
            "XRP_BRL (Natural Log Changes)",
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
            "XRP_INR (Natural Log Changes)",
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
            "XRP_ZAR (Natural Log Changes)",
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

# ---------- Label map (for LaTeX pretty printing) ----------
label_map = {
    "XRP_USD (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{USD})$",
    "XRP_GBP (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{GBP})$",
    "XRP_EUR (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{EUR})$",
    "XRP_JPY (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{JPY})$",
    "XRP_CNY (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{CNY})$",
    "XRP_BRL (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{BRL})$",
    "XRP_INR (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{INR})$",
    "XRP_ZAR (Natural Log Changes)": r"$\Delta \log(\mathrm{XRP}_{ZAR})$",
    "BCOM Index (Changes)": r"$\Delta \mathrm{Commodity}$",
    "USTWBGD  Index (Changes)": r"$\Delta \mathrm{Dollar}$",
    "VIX Index (Changes)": r"$\Delta \mathrm{VIX}$",
    "USGG10YR Index (Changes)": r"$\Delta \mathrm{10Y\ Yield}$",
    "USGG1M Index (Changes)": r"$\Delta \mathrm{1M\ Yield}$",
    "GTBRL10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTBRL1YR @BGN Corp (Changes)": r"$\Delta \mathrm{1Y\ Spread}$",
    "GTGBPII10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTGBP3MO @BGN Corp (Changes)": r"$\Delta \mathrm{3M\ Spread}$",
    "GTEUR10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTEUR3MO @BGN Corp (Changes)": r"$\Delta \mathrm{3M\ Spread}$",
    "GTJPY10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTJPY3MO @BGN Corp (Changes)": r"$\Delta \mathrm{3M\ Spread}$",
    "GTCNY10YR @CHBE Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTCNY1YR @CHBE Corp (Changes)": r"$\Delta \mathrm{1Y\ Spread}$",
    "GTINR10YR @NDSI Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTINR2YR @NDSI Corp (Changes)": r"$\Delta \mathrm{2Y\ Spread}$",
    "GTZAR10YR @BGN Corp (Changes)": r"$\Delta \mathrm{10Y\ Spread}$",
    "GTZAR1YR @BGN Corp (Changes)": r"$\Delta \mathrm{1Y\ Spread}$"
}

# ---------- Helpers: transform FROM LEVELS based on () suffix ----------
_space_re = re.compile(r"\s+")

def _clean(s: str) -> str:
    return _space_re.sub(" ", str(s).strip()).lower()

def level_name(name_with_suffix: str) -> str:
    # Strip the suffix to get the intended LEVEL name
    return (name_with_suffix
            .replace(" (Natural Log Changes)", "")
            .replace(" (Changes)", ""))

def build_lookup(df: pd.DataFrame) -> dict:
    # normalized header -> original header
    return {_clean(c): c for c in df.columns}

def resolve_level_col(df: pd.DataFrame, desired_level_name: str, original_with_suffix: str) -> str:
    """
    Resolve which column to treat as the LEVEL series.
    Priority:
      1) exact/normalized match to base name (no suffix)
      2) fallback: the suffixed header itself (many sheets use these as LEVEL headers)
      3) fuzzy match (>=0.85) on the base name
    """
    lut = build_lookup(df)
    base_key = _clean(desired_level_name)
    if base_key in lut:
        return lut[base_key]

    suff_key = _clean(original_with_suffix)
    if suff_key in lut:
        return lut[suff_key]

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
    lvl_col = resolve_level_col(df, level_name(name_with_suffix), name_with_suffix)
    s = pd.to_numeric(df[lvl_col], errors="coerce")

    if name_with_suffix.endswith("(Natural Log Changes)"):
        return np.log(s).diff()
    elif name_with_suffix.endswith("(Changes)"):
        return s.diff()
    else:
        raise ValueError(f"Unknown transform suffix in '{name_with_suffix}'")

def significance_stars(pval):
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.1:
        return "*"
    else:
        return ""

# ---------- Main: build tables ----------
with open("XRP_regressions.tex", "w") as f_out:
    for sheet, spec in regression_specs.items():
        df = pd.read_excel(xls, sheet_name=sheet)

        # Optional date handling
        if DATE_COL in df.columns:
            df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
            df = df.sort_values(DATE_COL)
            if START_DATE is not None:
                df = df[df[DATE_COL] >= pd.Timestamp(START_DATE)]
            if END_DATE is not None:
                df = df[df[DATE_COL] <= pd.Timestamp(END_DATE)]
        df = df.reset_index(drop=True)

        # Build FROM LEVELS (once per sheet)
        y_full = build_series_from_levels(df, spec["dependent"]).rename(spec["dependent"])
        X_all = {nm: build_series_from_levels(df, nm) for nm in spec["independents"]}
        X_all = pd.DataFrame(X_all)

        # Stepwise regressions
        models = []
        for i in range(1, len(spec["independents"]) + 1):
            subset = spec["independents"][:i]
            T = pd.concat([y_full, X_all[subset]], axis=1).dropna()
            if T.shape[0] < 20:
                raise ValueError(f"Too few rows after transforms in '{sheet}' (step {i}); got {T.shape[0]}")
            X = sm.add_constant(T[subset], has_constant="add")
            y = T[spec["dependent"]]
            model = sm.OLS(y, X).fit()
            models.append(model)

        # Build LaTeX
        lines = []
        lines.append("\\begin{table}[H]")
        lines.append("\\centering")
        lines.append(f"\\caption{{Ripple {sheet}}}")
        lines.append("\\resizebox{\\textwidth}{!}{%")
        lines.append("\\begin{tabular}{l" + "c" * len(models) + "}")
        lines.append("\\toprule")
        lines.append(f" & {' & '.join([f'({i+1})' for i in range(len(models))])} \\\\")
        lines.append("\\midrule")

        for var in spec["independents"]:
            label = label_map.get(var, var)
            coefs, ses = [], []
            for model in models:
                if var in model.params.index:
                    coef = model.params[var]
                    se = model.bse[var]
                    stars = significance_stars(model.pvalues[var])
                    coefs.append(f"{coef:.3f}{stars}")
                    ses.append(f"({se:.3f})")
                else:
                    coefs.append("")
                    ses.append("")
            lines.append(f"{label} & " + " & ".join(coefs) + " \\\\")
            lines.append(" & " + " & ".join(ses) + " \\\\")

        # Observations
        obs = [f"{int(m.nobs)}" for m in models]
        lines.append("\\midrule")
        lines.append("Observations & " + " & ".join(obs) + " \\\\")

        # Adj R^2
        r2 = [f"{m.rsquared_adj:.3f}" for m in models]
        lines.append("Adj. $R^2$ & " + " & ".join(r2) + " \\\\")

        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("}")  # close resizebox
        lines.append("\\begin{tablenotes}")
        lines.append("\\footnotesize")
        lines.append("Note: Dependent variable shown in caption. SE in parentheses. "
                     "*** p$<$0.01, ** p$<$0.05, * p$<$0.1.")
        lines.append("\\end{tablenotes}")
        lines.append("\\end{table}\n")

        f_out.write("\n".join(lines) + "\n\n")

print("All XRP regressions completed FROM LEVELS. Results saved to XRP_regressions.tex")
