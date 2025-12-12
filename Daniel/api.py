import requests
import time

class TraydnerAPI:
    """
    Lightweight wrapper for the Traydner trading API.
    Handles price fetching, candles, trades, balance, and market status.
    """

    BASE_URL = "https://traydner-186649552655.us-central1.run.app/api/remote"

    def __init__(self, api_key, timeout = 15):
        """
        Initialize the client.

        :param api_key: Your Traydner API key (Bearer token)
        :param timeout: HTTP timeout for all requests
        """
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    # ----------------------------
    # Internal request helper
    # ----------------------------
    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        r = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        r = requests.post(url, headers=self.headers, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ----------------------------
    # Public API Methods
    # ----------------------------

    def get_price(self, symbol):
        """
        Fetch latest price for a ticker.

        :param symbol: "BTC", "AAPL", "EURUSD", etc.
        """
        return self._get("price", {"symbol": symbol})

    def trade(self, symbol, side, quantity):
        """
        Execute a simulated trade.

        :param symbol: Ticker
        :param side: "buy" or "sell"
        :param quantityeger for stocks, float for crypto/forex
        """
        params = {"symbol": symbol, "side": side, "quantity": quantity}
        return self._post("trade", params)

    def get_balance(self):
        """Return your simulated account balance."""
        return self._get("balance")

    def get_history(self, symbol, resolution, limit = 500,
                    start_ts = None, end_ts = None):
        """
        Fetch historical candles.

        :param symbol: Ticker
        :param resolution: "1m","5m","1h","1d","D","W","M", etc.
        :param limit: number of candles (1–5000)
        :param start_ts: optional UNIX timestamp
        :param end_ts: optional UNIX timestamp
        """
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "limit": limit
        }
        if start_ts is not None:
            params["start_ts"] = start_ts
        if end_ts is not None:
            params["end_ts"] = end_ts

        return self._get("history", params)

    def market_status(self, symbol = None, market = None):
        """
        Get whether a market or symbol is currently open.

        :param symbol: overrides market if provided
        :param market: "stock", "crypto", or "forex"
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        if market:
            params["market"] = market

        return self._get("market_status", params)