# (Place in its own cell)
# Assumes the 'TraydnerAPI' class is defined/imported in a previous cell.

import math
import traceback 
from requests.exceptions import HTTPError
from typing import Optional, Dict, Any, List, Tuple
from TraydnerAPI import TraydnerAPI

class MeanReversionTrader:
    """
    Implements a mean reversion trading strategy (using Bollinger Bands)
    by consuming a TraydnerAPI client.
    
    This class is responsible for SIGNAL GENERATION, not execution.
    """
    
    def __init__(self, 
                 client: 'TraydnerAPI', # Using forward reference string
                 symbol: str, 
                 resolution: str, 
                 mean_period: int = 20, 
                 std_dev_multiplier: float = 2.0):
        """
        Initializes the mean reversion trader.

        Args:
            client (TraydnerAPI): An *instance* of the TraydnerAPI client.
            symbol (str): The symbol to trade (e.g., "BTC", "AAPL").
            resolution (str): The time resolution for candles (e.g., "1h", "D").
            mean_period (int): The lookback period for calculating the mean (SMA).
            std_dev_multiplier (float): The number of standard deviations
                                        to set the upper/lower bands.
        """
        self.client = client
        self.symbol = symbol
        self.resolution = resolution
        self.mean_period = mean_period
        self.std_dev_multiplier = std_dev_multiplier
        print(f"MeanReversionTrader initialized for {self.symbol}.")
        print(f"Strategy:   Mean Reversion (Bollinger Bands)")
        print(f"Symbol:     {self.symbol}")
        print(f"Resolution: {self.resolution}")
        print(f"Quantity:   {self.mean_period}")

    def _calculate_metrics(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Fetches historical data and calculates the mean, upper band, and lower band.

        Returns:
            Tuple[Optional[float], Optional[float], Optional[float]]:
            A tuple of (mean, upper_band, lower_band). Returns (None, None, None)
            if data is insufficient.
        """
        print(f"Fetching {self.mean_period} candles of {self.symbol}@{self.resolution} history...")
        
        try:
            # Fetch exactly the number of candles needed for the period
            history_data = self.client.get_history(
                symbol=self.symbol,
                resolution=self.resolution,
                limit=self.mean_period
            )
            
            history_list = history_data.get('history')
            
            # Add check to ensure history_list is actually a list
            if not history_list or not isinstance(history_list, list):
                print(f"Warning: 'history' key is missing, empty, or not a list. API response: {history_data}")
                return None, None, None

            if len(history_list) < self.mean_period:
                print(f"Warning: Insufficient historical data found ({len(history_list)} candles). Need {self.mean_period}.")
                return None, None, None
                
            # --- FIX: Changed 'c' to 'close' to match the API response ---
            closes = []
            for i, candle in enumerate(history_list):
                if not isinstance(candle, dict) or 'close' not in candle:
                    print(f"ERROR: Candle at index {i} is invalid or missing 'close' key. Data: {candle}")
                    raise KeyError(f"Candle at index {i} is invalid or missing 'close' key")
                
                # Also ensure the price is a valid number
                price = candle['close']
                if not isinstance(price, (int, float)):
                    print(f"ERROR: Price for candle {i} is not a number. Data: {candle}")
                    raise TypeError(f"Price for candle {i} is not a valid number.")
                    
                closes.append(price)
            # --- END FIX ---
            
            # Calculate metrics
            mean = sum(closes) / len(closes)
            
            # Calculate Standard Deviation
            sum_sq_diff = sum([(price - mean) ** 2 for price in closes])
            variance = sum_sq_diff / len(closes)
            std_dev = math.sqrt(variance)
            
            # Calculate bands
            upper_band = mean + (self.std_dev_multiplier * std_dev)
            lower_band = mean - (self.std_dev_multiplier * std_dev)
            
            return mean, upper_band, lower_band
            
        except HTTPError as e:
            print(f"Error fetching history: {e}")
            return None, None, None
        except Exception as e:
            # This will print the full traceback (file, line number, error type)
            print(f"An error occurred during metric calculation: {e}")
            traceback.print_exc()
            return None, None, None

    def get_signal(self) -> str:
        """
        Checks the current price against the bands and returns a trade signal.
        
        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        
        try:
            # 1. Check if the market is open
            status = self.client.get_market_status(symbol=self.symbol)
            if not status.get('isOpen', False):
                print(f"Market for {self.symbol} is closed. No signal generated.")
                return "HOLD"

            # 2. Get the trading bands
            mean, upper_band, lower_band = self._calculate_metrics()
            
            if mean is None:
                print("Could not calculate trading signals. No signal generated.")
                return "HOLD"

            # 3. Get the current price
            price_data = self.client.get_price(self.symbol)
            current_price = price_data.get('price')
            
            if current_price is None:
                print("Could not fetch current price. No signal generated.")
                return "HOLD"

            print(f"\n--- Strategy Check for {self.symbol} ---")
            print(f"Current Price: {current_price:.4f}")
            print(f"Lower Band:    {lower_band:.4f}")
            print(f"Mean (SMA):    {mean:.4f}")
            print(f"Upper Band:    {upper_band:.4f}")

            # 4. Make trading decision
            if current_price < lower_band:
                # Price is "oversold"
                print(f"\nGenerated Signal: BUY (Price {current_price:.4f} is BELOW lower band {lower_band:.4f})")
                return "BUY"
                
            elif current_price > upper_band:
                # Price is "overbought"
                print(f"\nGenerated Signal: SELL (Price {current_price:.4f} is ABOVE upper band {upper_band:.4f})")
                return "SELL"
                
            else:
                # Price is within the bands
                print("\nGenerated Signal: HOLD (Price is within the bands)")
                return "HOLD"

        except HTTPError as e:
            print(f"API Error during signal check: {e.response.status_code} - {e.response.text}")
            return "HOLD"
        except Exception as e:
            print(f"An unexpected error occurred during signal check: {e}")
            traceback.print_exc()
            return "HOLD"