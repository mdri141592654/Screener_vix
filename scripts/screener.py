import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

tickers = [
    "GLW","PTC","FRT","DUK","GE","DB1.DE","MET","NRG","NVDA","MTX.DE",
    "DG","BWA","BLK","AVGO","VNO","ROL","RSG","CB","LNT","WELL","KMI",
    "ALV.DE","NI","PG","PTC","BR","ATO","EVRG","L","CPB","ALL","BK","T",
    "DE","ETR","AIG","INVH","FRE.DE","CME","DTE.DE","SO","NDAQ","BLK","AEP",
    "BSX","EG","DTE","KR","GEV","JCI","WM","IRM","TDY","GIS","VTR","DG",
    "ROP","CBOE","PRU","PYPL","NVR","TRGP","BXP","CLX","APH","RMD","YUM",
    "PKG","GRMN","VRTX","HIG","KHC","MA","FOXA","AVB","ALLY","ESS","WTW",
    "PDG","STT","CSCO","HOLX","MAA","CNP","NOW","ROK","VNO","TGT","APA",
    "JPM","DAY","NSC","KIM","LRCX","BEN","ALGN","UBER","WDC","PARA","AXON",
    "GL","UAL"
]

def williams_vix_fix(close, low, high, length=22, bbl=20, mult=2.0):
    wvf = ((high.rolling(length).max() - low) / (high.rolling(length).max())) * 100
    sdev = mult * wvf.rolling(bbl).std()
    midline = wvf.rolling(bbl).mean()
    lower_band = midline - sdev
    return wvf < lower_band

result = {}

for ticker in tickers:
    try:
        data = yf.download(ticker, period="2y", interval="1h", progress=False)
        if data.empty: 
            continue

        signal = williams_vix_fix(data["Close"], data["Low"], data["High"])
        signal = signal.fillna(False)

        # Prüfen letzte 7 Kerzen zurück
        green_signals = []
        for i in range(0, 8):  
            if signal.iloc[-1 - i]:
                green_signals.append(i)

        result[ticker] = {
            "green_signals": green_signals,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

with open("data.json", "w") as f:
    json.dump(result, f, indent=2)
