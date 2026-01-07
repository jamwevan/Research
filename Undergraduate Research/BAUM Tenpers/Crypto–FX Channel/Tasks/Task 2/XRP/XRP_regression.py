import pandas as pd
import statsmodels.api as sm

# Load workbook
file = "program_data.xlsx"
xls = pd.ExcelFile(file)

# Regression specs for all countries (XRP instead of BTC/ETH/LTC/USDT)
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

# Label map (clean LaTeX-style labels for output tables)
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

def significance_stars(pval):
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.1:
        return "*"
    else:
        return ""

# One .tex file for all tables
with open("XRP_regressions.tex", "w") as f_out:
    for sheet, spec in regression_specs.items():
        df = pd.read_excel(xls, sheet_name=sheet)
        y = df[spec["dependent"]]

        models = []
        for i in range(1, len(spec["independents"]) + 1):
            X = df[spec["independents"][:i]]
            X = sm.add_constant(X)
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

        # Adj R2
        r2 = [f"{m.rsquared_adj:.3f}" for m in models]
        lines.append("Adj. $R^2$ & " + " & ".join(r2) + " \\\\")

        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("}")  # close resizebox
        lines.append("\\begin{tablenotes}")
        lines.append("\\footnotesize")
        lines.append("Note: Dependent variable in caption. SE in parentheses. "
                     "*** p$<$0.01, ** p$<$0.05, * p$<$0.1.")
        lines.append("\\end{tablenotes}")
        lines.append("\\end{table}\n")

        f_out.write("\n".join(lines) + "\n\n")

print("All XRP regressions completed. Results saved to XRP_regressions.tex")
