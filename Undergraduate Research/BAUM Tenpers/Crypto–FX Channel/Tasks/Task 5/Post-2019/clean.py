#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import statsmodels.api as sm

FILE = "program_data.xlsx"  # workbook with one sheet per country below

# ======== SPECS (TRANSFORM IS DICTATED BY THE SUFFIX) =========
regression_specs = {
    "US Regression": {
        "dependent": "SPXT Index (Natural Log Changes)",
        "independents": [
            "BTC_USD (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)"
        ],
        "currency": "Bitcoin USD",
    },
    "UK Regression": {
        "dependent": "UKX Index (Natural Log Changes)",
        "independents": [
            "BTC_GBP (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTGBPII10YR @BGN Corp (Changes)",
            "GTGBP3MO @BGN Corp (Changes)"
        ],
        "currency": "Bitcoin GBP",
    },
    "Eurozone Regression": {
        "dependent": "SXXP Index (Natural Log Changes)",
        "independents": [
            "BTC_EUR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTEUR10YR @BGN Corp (Changes)",
            "GTEUR3MO @BGN Corp (Changes)"
        ],
        "currency": "Bitcoin EUR",
    },
    "Japan Regression": {
        "dependent": "NKYTR Index (Natural Log Changes)",
        "independents": [
            "BTC_JPY (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTJPY10YR @BGN Corp (Changes)",
            "GTJPY3MO @BGN Corp (Changes)"
        ],
        "currency": "Bitcoin JPY",
    },
    "China Regression": {
        "dependent": "SHCOMP Index (Natural Log Changes)",
        "independents": [
            "BTC_CNY (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTCNY10YR @CHBE Corp (Changes)",
            "GTCNY1YR @CHBE Corp (Changes)"
        ],
        "currency": "Bitcoin CNY",
    },
    "Brazil Regression": {
        "dependent": "IBOV Index (Natural Log Changes)",
        "independents": [
            "BTC_BRL (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTBRL10YR @BGN Corp (Changes)",
            "GTBRL1YR @BGN Corp (Changes)"
        ],
        "currency": "Bitcoin BRL",
    },
    "India Regression": {
        "dependent": "NIFTY Index (Natural Log Changes)",
        "independents": [
            "BTC_INR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTINR10YR @NDSI Corp (Changes)",
            "GTINR2YR @NDSI Corp (Changes)"
        ],
        "currency": "Bitcoin INR",
    },
    "South Africa Regression": {
        "dependent": "JALSH Index (Natural Log Changes)",
        "independents": [
            "BTC_ZAR (Natural Log Changes)",
            "BCOM Index (Changes)",
            "USTWBGD  Index (Changes)",
            "VIX Index (Changes)",
            "USGG10YR Index (Changes)",
            "USGG1M Index (Changes)",
            "GTZAR10YR @BGN Corp (Changes)",
            "GTZAR1YR @BGN Corp (Changes)"
        ],
        "currency": "Bitcoin ZAR",
    },
}

# Pretty labels (exact keys are the raw column headers)
label_map = {
    "BTC_USD (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{USD})$",
    "BTC_GBP (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{GBP})$",
    "BTC_EUR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{EUR})$",
    "BTC_JPY (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{JPY})$",
    "BTC_CNY (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{CNY})$",
    "BTC_BRL (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{BRL})$",
    "BTC_INR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{INR})$",
    "BTC_ZAR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{ZAR})$",
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
    "GTZAR1YR @BGN Corp (Changes)": r"$\Delta \mathrm{1Y\ Spread}$",
}

# ======== Helpers ========
def transform_from_levels(level_series_name: str, df: pd.DataFrame) -> pd.Series:
    """
    Apply the transform implied by the column suffix to the LEVEL series in df.
    - '(Natural Log Changes)' -> log(level).diff()
    - '(Changes)'            -> level.diff()
    Returns a Series named exactly as the input column header.
    """
    if level_series_name.endswith("(Natural Log Changes)"):
        s = np.log(pd.to_numeric(df[level_series_name], errors="coerce")).diff()
    elif level_series_name.endswith("(Changes)"):
        s = pd.to_numeric(df[level_series_name], errors="coerce").diff()
    else:
        raise ValueError(f"Unknown suffix in '{level_series_name}'. Expected '(Natural Log Changes)' or '(Changes)'.")
    s.name = level_series_name
    return s

def stars(p):
    return "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.1 else ""))

# ======== Main ========
xls = pd.ExcelFile(FILE)
tables_out = []

for sheet_name, spec in regression_specs.items():
    # Read the sheet as-is (no sorting, no filtering, no index surgery)
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # Build transformed series from LEVELS
    y = transform_from_levels(spec["dependent"], df)
    X_cols = [transform_from_levels(col, df) for col in spec["independents"]]
    X_all = pd.concat(X_cols, axis=1)

    # Align rows strictly by non-missing across y and X (this sets the sample)
    base = pd.concat([y, X_all], axis=1).dropna()
    y_aligned = base[spec["dependent"]]
    X_aligned_all = base[spec["independents"]]

    # Stepwise models (1..k controls)
    models = []
    for k in range(1, len(spec["independents"]) + 1):
        Xk = sm.add_constant(X_aligned_all.iloc[:, :k], has_constant="add")
        models.append(sm.OLS(y_aligned, Xk).fit())

    # -------- LaTeX table --------
    lines = []
    lines.append(r"\begin{table}[H]")
    lines.append(r"\centering")
    lines.append(rf"\caption{{{spec['currency']} {sheet_name}}}")
    lines.append(r"\resizebox{\textwidth}{!}{%")
    lines.append(r"\begin{tabular}{l" + "c" * len(models) + "}")
    lines.append(r"\toprule")
    lines.append(" & " + " & ".join([f"({i+1})" for i in range(len(models))]) + r" \\")
    lines.append(r"\midrule")

    for raw in spec["independents"]:
        lab = label_map.get(raw, raw)
        coef_row, se_row = [], []
        for m in models:
            if raw in m.params.index:
                coef_row.append(f"{m.params[raw]:.3f}{stars(m.pvalues[raw])}")
                se_row.append(f"({m.bse[raw]:.3f})")
            else:
                coef_row.append("")
                se_row.append("")
        lines.append(f"{lab} & " + " & ".join(coef_row) + r" \\")
        lines.append(" & " + " & ".join(se_row) + r" \\")

    lines.append(r"\midrule")
    lines.append("Observations & " + " & ".join([f"{int(m.nobs)}" for m in models]) + r" \\")
    lines.append("Adj. $R^2$ & " + " & ".join([f"{m.rsquared_adj:.3f}" for m in models]) + r" \\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"}")
    lines.append(r"\begin{tablenotes}")
    lines.append(r"\footnotesize")
    lines.append(r"SE in parentheses. $^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.1$.")
    lines.append(r"\end{tablenotes}")
    lines.append(r"\end{table}")
    lines.append("")  # blank line

    tables_out.extend(lines)

with open("BTC_regressions.tex", "w") as f:
    f.write("\n".join(tables_out))

print("All regressions saved to BTC_regressions.tex")
