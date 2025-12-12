import time
import pandas as pd

class BuildCandles:
    def __init__(self, api_client, symbol, interval_sec=20, history_limit=100):
        self.api = api_client
        self.symbol = symbol
        self.interval_sec = interval_sec
        self.candles = []
        self.history_limit = history_limit

    def fetch_latest_candle(self):
        """Fetch current price from Traydner and make it a candle."""
        data = self.api.get_price(self.symbol)
        price = data["price"]
        ts = int(time.time())

        candle = {
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "timestamp": ts
        }
        self.candles.append(candle)

        if len(self.candles) > self.history_limit:
            self.candles = self.candles[-self.history_limit:]

        return pd.DataFrame(self.candles)

    def get_candles(self):
        """Return current candles without adding new one."""
        return pd.DataFrame(self.candles)

    def preload_history(self, api_client, symbol, limit=200):
        """
        Preload history using 1-minute candles, then break them into 20-second candles.
        """
        print(f"Preloading {limit} 1-minute candles...")

        history = api_client.get_history(symbol, resolution="1m", limit=limit)

        if not history or "candles" not in history:
            print("No historical data returned!")
            return

        one_min = history["candles"]

        for c in one_min:
            ts = c["timestamp"]

            opens  = [c["open"],  (c["open"]+c["close"])/2, c["close"]]
            closes = [(c["open"]+c["close"])/2, c["close"], c["close"]]
            highs  = [c["high"]]*3
            lows   = [c["low"]]*3

            for i in range(3):
                self.candles.append({
                    "timestamp": ts + i * 20000,
                    "open": opens[i],
                    "high": highs[i],
                    "low":  lows[i],
                    "close": closes[i]
                })

        print(f"Preload complete: {len(self.candles)} candles (20s resolution).")