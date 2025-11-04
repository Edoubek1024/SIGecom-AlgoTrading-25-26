import requests

class TraydnerAPI:
    """
    Traydner Remote Trading API — Python Interface
    -------------------------------------------------
    Base URL:
        https://traydner-186649552655.us-central1.run.app
    Authentication:
        Authorization: Bearer <YOUR_API_KEY>
    """

    BASE_URL = "https://traydner-186649552655.us-central1.run.app"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def _request(self, method: str, endpoint: str, params=None):
        """Internal: make a request and return JSON or raise for status."""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    # ---------- Public API Methods ---------- #

    def get_price(self, symbol: str):
        """Fetch latest price for a symbol (stock, crypto, or forex)."""
        return self._request("GET", "/api/remote/price", {"symbol": symbol})

    def make_trade(self, symbol: str, side: str, quantity):
        """Execute a simulated trade."""
        params = {"symbol": symbol, "side": side, "quantity": quantity}
        return self._request("POST", "/api/remote/trade", params)

    def get_balance(self):
        """Fetch your simulated account balance."""
        return self._request("GET", "/api/remote/balance")

    def get_history(self, symbol: str, resolution: str, limit: int = 500, start_ts=None, end_ts=None):
        """Fetch recent candles for a symbol and resolution."""
        params = {"symbol": symbol, "resolution": resolution, "limit": limit}
        if start_ts is not None:
            params["start_ts"] = start_ts
        if end_ts is not None:
            params["end_ts"] = end_ts
        return self._request("GET", "/api/remote/history", params)

    def get_market_status(self, symbol: str = None, market: str = None):
        """Returns { isOpen: bool } for a symbol or market."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        elif market:
            params["market"] = market
        return self._request("GET", "/api/remote/market_status", params)
