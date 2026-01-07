#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Prints ONLY the wedge variance ratio from PRICE LEVELS.
# Spec: y = Δlog(SPXT Index), x = Δlog(BTC_USD), controls = first differences of level controls.
# Output: WEDGE_VAR_RATIO = Var(e_y - e_x) / Var(e_x)

import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ====== EDIT HERE ONLY IF YOUR LEVEL COLUMN NAMES DIFFER ======
DATE = "Date"
SPXT = "SXXP Index"           # level
BTC  = "ETH_EUR"             # level
CTRL = [
    "BCOM Index",            # level
    "USTWBGD  Index",        # level
    "VIX Index",             # level
    "USGG10YR Index",        # level
    "USGG1M Index",          # level
    "GTEUR10YR @BGN Corp",   # level  <-- added
    "GTEUR3MO @BGN Corp",    # level  <-- added
]
# ===============================================================

def main(path: str):
    # read file (xlsx or csv)
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    # sort rows by date if present
    if DATE in df.columns:
        df[DATE] = pd.to_datetime(df[DATE], errors="coerce")
        df = df.sort_values(DATE).reset_index(drop=True)

    # coerce to numeric
    for c in [SPXT, BTC] + CTRL:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # TRANSFORMS from LEVELS
    y = np.log(df[SPXT]).diff()                 # Δlog stock
    x = np.log(df[BTC]).diff()                  # Δlog BTC
    C = pd.DataFrame({c: df[c].diff() for c in CTRL})   # Δ controls

    # align & drop NA
    data = pd.concat([y.rename("y"), x.rename("x"), C], axis=1).dropna()
    if len(data) < 10:
        raise ValueError("Not enough rows after transforms.")

    # residualize BOTH legs on the SAME Δ-controls
    Xc = sm.add_constant(C.loc[data.index], has_constant="add")
    e_y = sm.OLS(data["y"], Xc, missing="drop").fit().resid
    e_x = sm.OLS(data["x"], Xc, missing="drop").fit().resid

    # Wedge variance ratio
    wedge = e_y - e_x
    var_ex = float(np.var(e_x, ddof=0))
    if var_ex == 0.0:
        raise ZeroDivisionError("Var(e_x) is zero; cannot compute wedge ratio.")
    wedge_ratio = float(np.var(wedge, ddof=0) / var_ex)

    # PRINT ONLY the wedge ratio
    print(f"WEDGE_VAR_RATIO = {wedge_ratio:.6f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python wedge_diagnostics.py "program_data.xlsx"')
        sys.exit(1)
    main(sys.argv[1])
