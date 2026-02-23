import pandas as pd
from regress_core import build_features, run_all, run_state_only

XLSX = "Swap.xlsx"
SHEET = "post sofr"

def main():
    df_raw = pd.read_excel(XLSX, sheet_name=SHEET)

    # Oyakhi robustness: post-SOFR daily, q=0.75 (same 4 tables)
    df = build_features(df_raw, q=0.75, weekly=False)
    run_all(df, outdir="output", tag="post_q75_daily", maxlags=11)

    # Additional robustness: thresholds ONLY for STATE table (q70, q80)
    for q in [0.70, 0.80]:
        dfq = build_features(df_raw, q=q, weekly=False)
        run_state_only(dfq, outdir="output", tag=f"post_q{int(q*100)}_daily", maxlags=11)

if __name__ == "__main__":
    main()
