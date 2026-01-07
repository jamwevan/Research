import pandas as pd
import statsmodels.api as sm

# Load workbook
file = "program_data.xlsx"
xls = pd.ExcelFile(file)

# Regression specs for all countries
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
        "currency": "Bitcoin USD"
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
        "currency": "Bitcoin GBP"
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
        "currency": "Bitcoin EUR"
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
        "currency": "Bitcoin JPY"
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
        "currency": "Bitcoin CNY"
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
        "currency": "Bitcoin BRL"
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
        "currency": "Bitcoin INR"
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
        "currency": "Bitcoin ZAR"
    }
}

# Mapping raw column names to LaTeX-style symbolic labels
label_map = {
    "BTC_USD (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{USD})$",
    "BTC_GBP (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{GBP})$",
    "BTC_EUR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{EUR})$",
    "BTC_JPY (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{JPY})$",
    "BTC_CNY (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{CNY})$",
    "BTC_BRL (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{BRL})$",
    "BTC_INR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{INR})$",
    "BTC_ZAR (Natural Log Changes)": r"$\Delta \log(\mathrm{BTC}_{ZAR})$",
    "BCOM Index (Changes)": r"$\Delta Commodity$",
    "USTWBGD  Index (Changes)": r"$\Delta Dollar$",
    "VIX Index (Changes)": r"$\Delta VIX$",
    "USGG10YR Index (Changes)": r"$\Delta 10Y\ Yield$",
    "USGG1M Index (Changes)": r"$\Delta 1M\ Yield$",
    "GTBRL10YR @BGN Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTBRL1YR @BGN Corp (Changes)": r"$\Delta 1Y\ Spread$",
    "GTGBPII10YR @BGN Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTGBP3MO @BGN Corp (Changes)": r"$\Delta 3M\ Spread$",
    "GTEUR10YR @BGN Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTEUR3MO @BGN Corp (Changes)": r"$\Delta 3M\ Spread$",
    "GTJPY10YR @BGN Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTJPY3MO @BGN Corp (Changes)": r"$\Delta 3M\ Spread$",
    "GTCNY10YR @CHBE Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTCNY1YR @CHBE Corp (Changes)": r"$\Delta 1Y\ Spread$",
    "GTINR10YR @NDSI Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTINR2YR @NDSI Corp (Changes)": r"$\Delta 2Y\ Spread$",
    "GTZAR10YR @BGN Corp (Changes)": r"$\Delta 10Y\ Spread$",
    "GTZAR1YR @BGN Corp (Changes)": r"$\Delta 1Y\ Spread$"
}

def significance_stars(pval):
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.1:
        return "*"
    else:
        return ""

# Collect all tables into one LaTeX file
all_tables = []

for sheet, spec in regression_specs.items():
    df = pd.read_excel(xls, sheet_name=sheet)
    y = df[spec["dependent"]]

    models = []
    for i in range(1, len(spec["independents"]) + 1):
        X = df[spec["independents"][:i]]
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        models.append(model)

    # Table
    lines = []
    lines.append("\\begin{table}[H]")
    lines.append("\\centering")
    lines.append(f"\\caption{{{spec['currency']} {sheet}}}")
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

    # Obs + R2
    obs = [f"{int(m.nobs)}" for m in models]
    r2 = [f"{m.rsquared_adj:.3f}" for m in models]
    lines.append("\\midrule")
    lines.append("Observations & " + " & ".join(obs) + " \\\\")
    lines.append("Adj. $R^2$ & " + " & ".join(r2) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("}")  # close resizebox
    lines.append("\\begin{tablenotes}")
    lines.append("\\footnotesize")
    lines.append("Note: Dependent variable is log stock index (local currency). "
                 "SE in parentheses. *** p$<$0.01, ** p$<$0.05, * p$<$0.1.")
    lines.append("\\end{tablenotes}")
    lines.append("\\end{table}\n")

    all_tables.extend(lines)

# Save one .tex file
with open("BTC_regressions.tex", "w") as f:
    f.write("\n".join(all_tables))

print("All regressions saved to BTC_regressions.tex")
