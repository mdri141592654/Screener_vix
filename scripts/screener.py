import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

# Kürzere Tickerliste
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

# Funktion für VIX FIX
def vix_fix_signals(df, pd_len=22, bbl=20, mult=2.0, lb=50, pl=1.01):
    df["wvf"] = ((df["Close"].rolling(pd_len).max() - df["Low"]) / df["Close"].rolling(pd_len).max()) * 100
    sDev = mult * df["wvf"].rolling(bbl).std()
    midLine = df["wvf"].rolling(bbl).mean()
    upperBand = midLine + sDev
    rangeHigh = df["wvf"].rolling(lb).max() * pl
    df["isGreenBar"] = (df["wvf"] >= upperBand) | (df["wvf"] >= rangeHigh)
    return df

# Daten sammeln
green_signals = []
end_date = datetime.today()
start_date = end_date - timedelta(days=100)

for ticker in tickers:
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)
        if data.empty: 
            continue
        df = vix_fix_signals(data)

        # Metadaten holen
        info = {}
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            pass
        company_name = info.get("longName", "Unbekannt")

        # Prüfen: innerhalb der letzten 3 Tage grünes Signal?
        for offset in range(0, 3):
            if bool(df["isGreenBar"].iloc[-1 - offset]):
                price = float(round(df["Close"].iloc[-1], 2))
                green_signals.append({
                    "ticker": str(ticker),
                    "company": str(company_name),
                    "days_since": int(offset),
                    "last_price": price
                })
                break
    except Exception:
        continue

# Speichern in JSON
result = {
    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "signals": green_signals
}

with open("data/results.json", "w") as f:
    json.dump(result, f, indent=2)

print("Aktualisierte Ergebnisse gespeichert in data/results.json")
