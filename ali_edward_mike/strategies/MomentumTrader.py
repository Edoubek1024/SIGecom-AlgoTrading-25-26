# Momentum Trading Strategy using RSI (Relative Strength Index)
# Assumes the 'TraydnerAPI' class is defined/imported in a previous cell.

import math
import traceback 
from requests.exceptions import HTTPError
from typing import Optional, Dict, Any, List, Tuple
from TraydnerAPI import TraydnerAPI

class MomentumTrader:
    """
    Implements a momentum trading strategy using RSI (Relative Strength Index)
    by consuming a TraydnerAPI client.
    
    RSI measures the speed and magnitude of recent price changes to identify
    overbought (RSI > 70) or oversold (RSI < 30) conditions.
    
    This class is responsible for SIGNAL GENERATION, not execution.
    """
    
    def __init__(self, 
                 client: 'TraydnerAPI',
                 symbol: str, 
                 resolution: str, 
                 rsi_period: int = 14,
                 oversold_threshold: float = 30.0,
                 overbought_threshold: float = 70.0):
        """
        Initializes the momentum trader.

        Args:
            client (TraydnerAPI): An *instance* of the TraydnerAPI client.
            symbol (str): The symbol to trade (e.g., "BTC", "ETH", "AAPL").
            resolution (str): The time resolution for candles (e.g., "1h", "D", "15m").
            rsi_period (int): The lookback period for RSI calculation (typically 14).
            oversold_threshold (float): RSI value below which is considered oversold (default 30).
            overbought_threshold (float): RSI value above which is considered overbought (default 70).
        """
        self.client = client
        self.symbol = symbol
        self.resolution = resolution
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        print(f"MomentumTrader initialized for {self.symbol}.")
        print(f"Strategy:   Momentum (RSI)")
        print(f"Symbol:     {self.symbol}")
        print(f"Resolution: {self.resolution}")
        print(f"RSI Period: {self.rsi_period}")
        print(f"Oversold:   < {self.oversold_threshold}")
        print(f"Overbought: > {self.overbought_threshold}")

    def _calculate_rsi(self) -> Optional[float]:
        """
        Fetches historical data and calculates the RSI.

        Returns:
            Optional[float]: The current RSI value, or None if calculation fails.
        """
        print(f"Fetching {self.rsi_period + 1} candles of {self.symbol}@{self.resolution} history for RSI...")
        
        try:
            # Need period + 1 candles to calculate period changes
            history_data = self.client.get_history(
                symbol=self.symbol,
                resolution=self.resolution,
                limit=self.rsi_period + 1
            )
            
            history_list = history_data.get('history')
            
            # Validate history data
            if not history_list or not isinstance(history_list, list):
                print(f"Warning: 'history' key is missing, empty, or not a list. API response: {history_data}")
                return None

            if len(history_list) < self.rsi_period + 1:
                print(f"Warning: Insufficient historical data found ({len(history_list)} candles). Need {self.rsi_period + 1}.")
                return None
            
            # Extract closing prices
            closes = []
            for i, candle in enumerate(history_list):
                if not isinstance(candle, dict) or 'close' not in candle:
                    print(f"ERROR: Candle at index {i} is invalid or missing 'close' key. Data: {candle}")
                    raise KeyError(f"Candle at index {i} is invalid or missing 'close' key")
                
                price = candle['close']
                if not isinstance(price, (int, float)):
                    print(f"ERROR: Price for candle {i} is not a number. Data: {candle}")
                    raise TypeError(f"Price for candle {i} is not a valid number.")
                    
                closes.append(price)
            
            # Calculate price changes
            gains = []
            losses = []
            
            for i in range(1, len(closes)):
                change = closes[i] - closes[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            # Calculate average gain and average loss
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)
            
            # Avoid division by zero
            if avg_loss == 0:
                return 100.0  # If no losses, RSI is 100
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except HTTPError as e:
            print(f"Error fetching history: {e}")
            return None
        except Exception as e:
            print(f"An error occurred during RSI calculation: {e}")
            traceback.print_exc()
            return None

    def get_signal(self) -> str:
        """
        Checks the current RSI and returns a trade signal.
        
        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        
        try:
            # 1. Check if the market is open
            status = self.client.get_market_status(symbol=self.symbol)
            if not status.get('isOpen', False):
                print(f"Market for {self.symbol} is closed. No signal generated.")
                return "HOLD"

            # 2. Calculate RSI
            rsi = self._calculate_rsi()
            
            if rsi is None:
                print("Could not calculate RSI. No signal generated.")
                return "HOLD"

            # 3. Get the current price for display
            price_data = self.client.get_price(self.symbol)
            current_price = price_data.get('price')
            
            if current_price is None:
                print("Could not fetch current price. No signal generated.")
                return "HOLD"

            print(f"\n--- Strategy Check for {self.symbol} ---")
            print(f"Current Price: {current_price:.4f}")
            print(f"Current RSI:   {rsi:.2f}")
            print(f"Oversold:      < {self.oversold_threshold}")
            print(f"Overbought:    > {self.overbought_threshold}")

            # 4. Make trading decision based on RSI
            if rsi < self.oversold_threshold:
                # RSI indicates oversold - potential buy opportunity
                print(f"\nGenerated Signal: BUY (RSI {rsi:.2f} is BELOW oversold threshold {self.oversold_threshold})")
                return "BUY"
                
            elif rsi > self.overbought_threshold:
                # RSI indicates overbought - potential sell opportunity
                print(f"\nGenerated Signal: SELL (RSI {rsi:.2f} is ABOVE overbought threshold {self.overbought_threshold})")
                return "SELL"
                
            else:
                # RSI is neutral
                print(f"\nGenerated Signal: HOLD (RSI {rsi:.2f} is in neutral zone)")
                return "HOLD"

        except HTTPError as e:
            print(f"API Error during signal check: {e.response.status_code} - {e.response.text}")
            return "HOLD"
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return "HOLD"
