import requests
from requests.exceptions import HTTPError
from typing import Optional, Dict, Any, List

class TraydnerAPI:
    """
    A Python client for the Traydner API.
    
    This class manages authentication and provides methods for each
    of the API endpoints documented.
    """
    
    def __init__(self, api_key: str):
        """
        Initializes the API client.

        Args:
            api_key (str): Your API key (Bearer token).
        """
        if not api_key:
            raise ValueError("API key is required.")
            
        self.base_url = "https://traydner-186649552655.us-central1.run.app/api/remote"
        self._api_key = api_key
        
        # Use a session to persist headers across all requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json"
        })

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal helper method to make API requests.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint path (e.g., "/price").
            params (Optional[Dict[str, Any]]): Query parameters for the request.

        Returns:
            Dict[str, Any]: The JSON response from the API.

        Raises:
            HTTPError: If the API returns an unsuccessful status code.
        """
        url = self.base_url + endpoint
        
        # Filter out optional parameters that are None
        if params:
            cleaned_params = {k: v for k, v in params.items() if v is not None}
        else:
            cleaned_params = None

        try:
            response = self.session.request(method, url, params=cleaned_params)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
            raise
        except Exception as err:
            print(f"An other error occurred: {err}")
            raise

    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches the latest price for a given symbol.

        Args:
            symbol (str): Ticker symbol (e.g., "AAPL", "BTC", "EUR").

        Returns:
            Dict[str, Any]: API response with price data.
        """
        return self._request("GET", "/price", params={"symbol": symbol})

    def execute_trade(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Executes a simulated trade.

        Args:
            symbol (str): Ticker symbol.
            side (str): 'buy' or 'sell'.
            quantity (float): Number of units. Integers required for stocks.

        Returns:
            Dict[str, Any]: API response confirming the trade.
        """
        if side not in ['buy', 'sell']:
            raise ValueError("Side must be 'buy' or 'sell'.")
            
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity
        }
        return self._request("POST", "/trade", params=params)

    def get_balance(self) -> Dict[str, Any]:
        """
        Fetches the simulated account balance for the authenticated user.

        Returns:
            Dict[str, Any]: API response with balance information.
        """
        return self._request("GET", "/balance")

    def get_history(self, 
                    symbol: str, 
                    resolution: str, 
                    start_ts: Optional[int] = None, 
                    end_ts: Optional[int] = None, 
                    limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetches recent candles (historical data) for a symbol.

        Args:
            symbol (str): Ticker symbol.
            resolution (str): Time resolution (e.g., "1m", "5m", "1h", "D").
            start_ts (Optional[int]): Start timestamp (Unix seconds).
            end_ts (Optional[int]): End timestamp (Unix seconds).
            limit (Optional[int]): Max number of candles (1-5000, default 500).

        Returns:
            Dict[str, Any]: API response with historical data.
        """
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "limit": limit
        }
        return self._request("GET", "/history", params=params)

    def get_market_status(self, 
                          symbol: Optional[str] = None, 
                          market: Optional[str] = None) -> Dict[str, bool]:
        """
        Returns the market status (open or closed).

        Args:
            symbol (Optional[str]): Ticker symbol. Takes precedence over 'market'.
            market (Optional[str]): Market type ("stock", "crypto", "forex").

        Returns:
            Dict[str, bool]: API response, e.g., {"isOpen": true}.
        """
        if not symbol and not market:
            raise ValueError("Either 'symbol' or 'market' must be provided.")
            
        params = {
            "symbol": symbol,
            "market": market
        }
        return self._request("GET", "/market_status", params=params)
