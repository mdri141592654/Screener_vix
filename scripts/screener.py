import yfinance as yf
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Ordner für Plots + HTML
os.makedirs("data/plots", exist_ok=True)
os.makedirs("docs/details", exist_ok=True)

tickers = [
    "GLW","PTC","FRT","DUK","GE","DB1.DE","MET","NRG","NVDA","MTX.DE","DG","BWA","BLK",
    "AVGO","VNO","ROL","RSG","CB","LNT","WELL","KMI","ALV.DE","NI","PG","PTC","BR","ATO",
    "EVRG","L","CPB","ALL","BK","T","DE","ETR","AIG","INVH","FRE.DE","CME","DTE.DE","SO",
    "NDAQ","BLK","AEP","BSX","EG","DTE","KR","GEV","JCI","WM","IRM","TDY","GIS","VTR","DG",
    "ROP","CBOE","PRU","PYPL","NVR","TRGP","BXP","CLX","APH","RMD","YUM","PKG","GRMN","VRTX",
    "HIG","KHC","MA","FOXA","AVB","ALLY","ESS","WTW","PDG","STT","CSCO","HOLX","MAA","CNP",
    "NOW","ROK","VNO","TGT","APA","JPM","DAY","NSC","KIM","LRCX","BEN","ALGN","UBER","WDC",
    "PARA","AXON","GL","UAL"
]

def vix_fix_signals(df, pd_len=22, bbl=20, mult=2.0, lb=50, pl=1.01):
    df["wvf"] = ((df["Close"].rolling(pd_len).max() - df["Low"]) / df["Close"].rolling(pd_len).max()) * 100
    sDev = mult * df["wvf"].rolling(bbl).std()
    midLine = df["wvf"].rolling(bbl).mean()
    upperBand = midLine + sDev
    rangeHigh = df["wvf"].rolling(lb).max() * pl
    df["isGreenBar"] = (df["wvf"] >= upperBand) | (df["wvf"] >= rangeHigh)
    return df

def analyze_and_plot(df, symbol, days_since):
    look_forward = 21
    df = vix_fix_signals(df)
    green_signals = df[df["isGreenBar"]].index.tolist()

    if not green_signals:
        return None

    changes = {lag: [] for lag in range(1, look_forward + 1)}
    for idx in green_signals:
        signal_close = df.loc[idx, "Close"]
        for lag in range(1, look_forward + 1):
            if idx + lag < len(df):
                future_close = df.loc[idx + lag, "Close"]
                pct_change = (future_close - signal_close) / signal_close * 100
                changes[lag].append(pct_change)

    averages, stds = {}, {}
    for lag, vals in changes.items():
        if vals:
            averages[lag] = np.mean(vals)
            stds[lag] = np.std(vals)

    if averages:
        lags = list(averages.keys())
        avgs = [averages[lag] for lag in lags]
        devs = [stds[lag] for lag in lags]
        plt.figure(figsize=(8, 5))
        plt.plot(lags, avgs, marker="o", color="lime", label="Durchschnitt")
        plt.fill_between(lags,
                         [avgs[i] - devs[i] for i in range(len(lags))],
                         [avgs[i] + devs[i] for i in range(len(lags))],
                         color="lime", alpha=0.2, label="±1 Std")
        plt.axhline(y=0, color="r", linestyle="--")
        plt.xlabel("Kerzen nach Signal")
        plt.ylabel("% Veränderung")
        plt.title(f"Signal-Analyse {symbol}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"data/plots/{symbol}.png")
        plt.close()

# Sammeln
green_signals = []
end_date = datetime.today()
start_date = end_date - timedelta(days=730)  # 2 Jahre

for ticker in tickers:
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if data.empty:
            continue
        df = vix_fix_signals(data)

        for offset in range(0, 3):
            if df["isGreenBar"].iloc[-1 - offset]:
                info = yf.Ticker(ticker).info
                company_name = info.get("longName", "Unbekannt")

                # Analyse & Plot
                analyze_and_plot(data.reset_index(), ticker, offset)

                green_signals.append({
                    "ticker": ticker,
                    "company": company_name,
                    "days_since": offset
                })
                break
    except Exception:
        continue

result = {
    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "signals": green_signals
}

with open("data/results.json", "w") as f:
    json.dump(result, f, indent=2)

print("Aktualisierte Ergebnisse gespeichert in data/results.json")

# --------------------------------------------------
# HTML GENERATOR
# --------------------------------------------------

# Hauptseite (index.html)
index_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Signal Übersicht</title>
<style>
body { font-family: Arial; font-size: 20px; }
a { text-decoration: none; color: blue; }
</style>
</head>
<body>
<h1>Aktuelle Signale</h1>
<ul>
"""
for s in green_signals:
    index_html += f'<li><a href="details/{s["ticker"]}.html">{s["ticker"]}</a></li>\n'
index_html += """
</ul>
</body>
</html>
"""
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# Detailseiten
for s in green_signals:
    detail_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{s["ticker"]} Details</title>
<style>
body {{ font-family: Arial; font-size: 18px; }}
a {{ text-decoration: none; color: blue; }}
</style>
</head>
<body>
<a href="../index.html">&larr; Zurück</a>
<h1>{s["ticker"]} – {s["company"]}</h1>
<p><b>Signal vor:</b> {s["days_since"]} Tagen</p>
<p><b>Daten aktualisiert:</b> {result["timestamp"]}</p>
<img src="../data/plots/{s["ticker"]}.png" alt="Chart {s["ticker"]}" style="max-width:90%;">
</body>
</html>
"""
    with open(f"docs/details/{s['ticker']}.html", "w", encoding="utf-8") as f:
        f.write(detail_html)

print("HTML-Seiten erstellt unter docs/")
