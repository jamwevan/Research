import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

TAUS = [2, 5, 10, 20]

def _ensure_date(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    elif "Unnamed: 0" in df.columns:
        df = df.rename(columns={"Unnamed: 0": "Date"})
        df["Date"] = pd.to_datetime(df["Date"])
    else:
        raise ValueError("No Date column found (expected 'Date' or 'Unnamed: 0').")

    df = df.sort_values("Date").reset_index(drop=True)
    return df

def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def build_features(df_raw: pd.DataFrame, q: float = 0.75, weekly: bool = False) -> pd.DataFrame:
    df = df_raw.copy()
    df = _ensure_date(df)

    needed = [
        "VIX Index", "MOVE Index", "LUACTRUU Index", "GT10 @BGN Govt",
        "USSP2 BLP Curncy", "USSP5 BLP Curncy", "USSP10 BLP Curncy", "USSP20 BLP Curncy"
    ]
    _coerce_numeric(df, needed)

    if weekly:
        df = (
            df.set_index("Date")
              .resample("W-FRI")
              .last()
              .dropna(how="all")
              .reset_index()
        )

    # First differences
    df["dCredit"] = df["LUACTRUU Index"].diff()
    df["dy10"] = df["GT10 @BGN Govt"].diff()
    for tau in TAUS:
        df[f"dSS{tau}"] = df[f"USSP{tau} BLP Curncy"].diff()

    # Thresholds computed on THIS sample
    vix_p = df["VIX Index"].quantile(q)
    move_p = df["MOVE Index"].quantile(q)

    df["Funding"] = ((df["VIX Index"] > vix_p) & (df["dy10"] < 0)).astype(int)
    df["Inflation"] = ((df["MOVE Index"] > move_p) & (df["dy10"] > 0)).astype(int)

    # Standardized intensity vars
    df["VIX_z"] = (df["VIX Index"] - df["VIX Index"].mean()) / df["VIX Index"].std(ddof=0)
    df["MOVE_z"] = (df["MOVE Index"] - df["MOVE Index"].mean()) / df["MOVE Index"].std(ddof=0)

    return df

def _ols_hac(y: pd.Series, X: pd.DataFrame, maxlags: int = 11):
    Xc = sm.add_constant(X, has_constant="add")
    return sm.OLS(y, Xc, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})

def _format_cell(beta, se):
    if pd.isna(beta) or pd.isna(se):
        return ""
    t = beta / se if se != 0 else np.nan
    star = ""
    if np.isfinite(t):
        at = abs(t)
        if at >= 2.58: star = "***"
        elif at >= 1.96: star = "**"
        elif at >= 1.64: star = "*"
    return f"{beta:.4f}{star}\n({se:.4f})"

def _table_from_models(models: dict, params: list[str], rownames: list[str]) -> pd.DataFrame:
    cols = []
    for tau, m in models.items():
        col = {}
        for p, rn in zip(params, rownames):
            beta = m.params.get(p, np.nan)
            se = m.bse.get(p, np.nan)
            col[rn] = _format_cell(beta, se)
        cols.append(pd.Series(col, name=f"τ={tau}"))
    tab = pd.concat(cols, axis=1)
    # IMPORTANT: prevent "NaN" printing in LaTeX
    return tab.replace({np.nan: ""})

def run_all(df_feat: pd.DataFrame, outdir: str, tag: str, maxlags: int = 11) -> None:
    os.makedirs(outdir, exist_ok=True)

    # (5.1) Baseline: dCredit ~ dSS_tau
    models = {}
    for tau in TAUS:
        models[tau] = _ols_hac(df_feat["dCredit"], df_feat[[f"dSS{tau}"]], maxlags=maxlags)

    # Clean baseline table: diagonal form (only each tau's own coefficient)
    baseline = pd.DataFrame(
        index=[f"β (ΔSS{t})" for t in TAUS],
        columns=[f"τ={t}" for t in TAUS],
        dtype=object
    )
    for tau in TAUS:
        m = models[tau]
        baseline.loc[f"β (ΔSS{tau})", f"τ={tau}"] = _format_cell(
            m.params.get(f"dSS{tau}"), m.bse.get(f"dSS{tau}")
        )

    # FIX: remove NaN so LaTeX doesn't show it
    baseline = baseline.replace({np.nan: ""})
    baseline.to_latex(os.path.join(outdir, f"{tag}_baseline.tex"), escape=False)

    # (5.2) State-dependent: dCredit ~ dSS*Funding + dSS*Inflation
    models = {}
    for tau in TAUS:
        X = pd.DataFrame({
            "SS_Funding": df_feat[f"dSS{tau}"] * df_feat["Funding"],
            "SS_Inflation": df_feat[f"dSS{tau}"] * df_feat["Inflation"],
        })
        models[tau] = _ols_hac(df_feat["dCredit"], X, maxlags=maxlags)

    state = _table_from_models(
        models=models,
        params=["SS_Funding", "SS_Inflation"],
        rownames=["β_F (ΔSS×Funding)", "β_I (ΔSS×Inflation)"]
    )
    state.to_latex(os.path.join(outdir, f"{tag}_state.tex"), escape=False)

    # (5.3) Intensity: dCredit ~ dSS + dSS*VIX_z + dSS*MOVE_z
    models = {}
    for tau in TAUS:
        X = pd.DataFrame({
            "SS": df_feat[f"dSS{tau}"],
            "SSxVIX": df_feat[f"dSS{tau}"] * df_feat["VIX_z"],
            "SSxMOVE": df_feat[f"dSS{tau}"] * df_feat["MOVE_z"],
        })
        models[tau] = _ols_hac(df_feat["dCredit"], X, maxlags=maxlags)

    intensity = _table_from_models(
        models=models,
        params=["SS", "SSxVIX", "SSxMOVE"],
        rownames=["β (ΔSS)", "γ_V (ΔSS×VIX_z)", "γ_M (ΔSS×MOVE_z)"]
    )
    intensity.to_latex(os.path.join(outdir, f"{tag}_intensity.tex"), escape=False)

    # (6) Rate control: dCredit ~ dSS + dy10
    models = {}
    for tau in TAUS:
        X = pd.DataFrame({
            "SS": df_feat[f"dSS{tau}"],
            "dy10": df_feat["dy10"],
        })
        models[tau] = _ols_hac(df_feat["dCredit"], X, maxlags=maxlags)

    rate = _table_from_models(
        models=models,
        params=["SS", "dy10"],
        rownames=["β (ΔSS)", "δ (Δy10)"]
    )
    rate.to_latex(os.path.join(outdir, f"{tag}_rate_control.tex"), escape=False)

def run_state_only(df_feat: pd.DataFrame, outdir: str, tag: str, maxlags: int = 11) -> None:
    os.makedirs(outdir, exist_ok=True)

    models = {}
    for tau in TAUS:
        X = pd.DataFrame({
            "SS_Funding": df_feat[f"dSS{tau}"] * df_feat["Funding"],
            "SS_Inflation": df_feat[f"dSS{tau}"] * df_feat["Inflation"],
        })
        models[tau] = _ols_hac(df_feat["dCredit"], X, maxlags=maxlags)

    state = _table_from_models(
        models=models,
        params=["SS_Funding", "SS_Inflation"],
        rownames=["β_F (ΔSS×Funding)", "β_I (ΔSS×Inflation)"]
    )
    state.to_latex(os.path.join(outdir, f"{tag}_state.tex"), escape=False)
