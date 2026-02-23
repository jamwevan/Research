import pandas as pd
from regress_core import build_features, run_all

XLSX = "Swap.xlsx"
SHEET = "presofr"

def main():
    df_raw = pd.read_excel(XLSX, sheet_name=SHEET)

    # Oyakhi MAIN: pre-SOFR daily, q=0.75
    df = build_features(df_raw, q=0.75, weekly=False)
    run_all(df, outdir="output", tag="pre_q75_daily", maxlags=11)

if __name__ == "__main__":
    main()
