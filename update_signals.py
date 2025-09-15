import yfinance as yf
import pandas as pd
import numpy as np
import json

# Liste der Aktien
tickers = [
    "GLW","PTC","FRT","DUK","GE","DB1.DE","MET","NRG","NVDA","MTX.DE","DG","BWA","BLK","AVGO",
    "VNO","ROL","RSG","CB","LNT","WELL","KMI","ALV.DE","NI","PG","PTC","BR","ATO","EVRG","L","CPB",
    "ALL","BK","T","DE","ETR","AIG","INVH","FRE.DE","CME","DTE.DE","SO","NDAQ","BLK","AEP","BSX",
    "EG","DTE","KR","GEV","JCI","WM","IRM","TDY","GIS","VTR","DG","ROP","CBOE","PRU","PYPL","NVR",
    "TRGP","BXP","CLX","APH","RMD","YUM","PKG","GRMN","VRTX","HIG","KHC","MA","FOXA","AVB","ALLY",
    "ESS","WTW","PDG","STT","CSCO","HOLX","MAA","CNP","NOW","ROK","VNO","TGT","APA","JPM","DAY",
    "NSC","KIM","LRCX","BEN","ALGN","UBER","WDC","PARA","AXON","GL","UAL"
]

# Parameter wie im Pine Script
pd_ = 22
bbl = 20
mult = 2.0
lb = 50
pl = 1.01

# Funktion: VIX Fix Grün
def vix_fix_green(df):
    wvf = ((df['Close'].rolling(pd_).max() - df['Low']) / df['Close'].rolling(pd_).max()) * 100
    sDev = mult * wvf.rolling(bbl).std()
    midLine = wvf.rolling(bbl).mean()
    upperBand = midLine + sDev
    rangeHigh = wvf.rolling(lb).max() * pl
    isGreen = (wvf >= upperBand) | (wvf >= rangeHigh)
    return isGreen.fillna(False)

results = []

for ticker in tickers:
    try:
        df = yf.download(ticker, interval="1d", period="1y", progress=False)
        if df.empty:
            continue

        df = df.dropna(subset=['Close', 'High', 'Low'])
        df['Green'] = vix_fix_green(df)

        # Letzte 6 Kerzen prüfen (0–5 Balken zurück)
        last_rows = df.tail(6)
        signal_idx = np.where(last_rows['Green'].values)[0]

        if len(signal_idx) > 0:
            bars_back = 5 - signal_idx[-1]
            price = float(round(df['Close'].iloc[-1], 2))

            # Name sicher extrahieren
            name = ""
            try:
                info = yf.Ticker(ticker).info
                name = str(info.get("shortName", ""))
            except Exception:
                name = ""

            results.append({
                "ticker": str(ticker),
                "name": name,
                "price": price,
                "signal_bars_back": int(bars_back),
                "date": str(df.index[-1].date())
            })

        # Debug-Ausgabe (optional)
        print(f"{ticker}: {len(signal_idx)} Signale gefunden")
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# JSON speichern
with open("./signals.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Fertig! {len(results)} Aktien mit grünen Signalen gefunden.")
