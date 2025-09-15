import yfinance as yf
import pandas as pd
import numpy as np
import json

tickers = [ ... ]  # deine Liste

def vix_fix_green(df, pd_=22, bbl=20, mult=2.0, lb=50, pl=1.01):
    wvf = ((df['Close'].rolling(pd_).max() - df['Low']) / df['Close'].rolling(pd_).max()) * 100
    sDev = mult * wvf.rolling(bbl).std()
    midLine = wvf.rolling(bbl).mean()
    upperBand = midLine + sDev
    rangeHigh = wvf.rolling(lb).max() * pl
    isGreen = (wvf >= upperBand) | (wvf >= rangeHigh)
    return isGreen

results = []

for ticker in tickers:
    try:
        df = yf.download(ticker, interval="1d", period="6mo", progress=False)
        if df.empty: 
            continue

        df["Green"] = vix_fix_green(df)
        last_rows = df.tail(6)
        signal_idx = np.where(last_rows["Green"].values)[0]

        if len(signal_idx) > 0:
            bars_back = 5 - signal_idx[-1]
            price = float(round(df["Close"].iloc[-1], 2))

            # Firmenname sicher extrahieren
            name = ""
            try:
                name = str(yf.Ticker(ticker).info.get("shortName", ""))
            except Exception:
                name = ""

            results.append({
                "ticker": str(ticker),
                "name": name,
                "price": price,
                "signal_bars_back": int(bars_back),
                "date": str(df.index[-1].date())
            })
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

with open("signals.json", "w") as f:
    json.dump(results, f, indent=2)
