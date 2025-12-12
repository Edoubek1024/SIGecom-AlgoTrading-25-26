import time
import pandas as pd
from collections import deque
from display import ConsoleDisplay
from candles import BuildCandles
from ta.volatility import BollingerBands, AverageTrueRange
import api

# ##########################
# Strategy: SMA + Bollinger + ATR
# ##########################
class ARIMA:
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, df):
        # Not enough data
        if len(df) < self.long_window:
            return 0

        close = df['close']

        # Bollinger Bands
        bb = BollingerBands(close=close, window=self.long_window, window_dev=2)
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_lower"] = bb.bollinger_lband()

        # ATR
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=close, window=self.long_window)
        df['atr'] = atr.average_true_range()
        latest_atr = df['atr'].iloc[-1]

        sma_short = close[-self.short_window:].mean()
        sma_long = close[-self.long_window:].mean()
        latest_close = close.iloc[-1]
        bb_upper = df["bb_upper"].iloc[-1]
        bb_lower = df["bb_lower"].iloc[-1]

        threshold = 1.5 * latest_atr

        if sma_short > sma_long + threshold and latest_close < bb_upper:
            print(sma_short, ">", sma_long + threshold, "AND", latest_close, "<", bb_upper)
            return 1  # BUY
        elif sma_short < sma_long - threshold and latest_close > bb_lower:
            print(sma_short, "<", sma_long - threshold, "AND", latest_close, ">", bb_lower)
            return -1  # SELL
        print(sma_short, "<", sma_long + threshold, "AND", latest_close, ">", bb_upper)
        print(sma_short, ">", sma_long - threshold, "AND", latest_close, "<", bb_lower)
        return 0  # HOLD

# ##########################
# Trader Bot
# ##########################
class TraderBot:
    def __init__(self, api_client, strategy, candle_builder, symbol, display=None, trade_size=1):
        self.api = api_client
        self.strategy = strategy
        self.builder = candle_builder
        self.symbol = symbol
        self.trade_size = trade_size
        self.display = display

    def run(self, interval=20):
        print(f"Starting trading bot for {self.symbol} with interval {interval}s...\n")
        while True:
            # Fetch the latest candle every 20 seconds
            candles = self.builder.get_candles()
            print(f"Candles fetched: {len(candles)}")

            signal = self.strategy.generate_signal(candles)

            if signal == 1:
                trade = self.api.trade(self.symbol, "buy", self.trade_size)
                print(f"BUY executed at {trade['price']}")
            elif signal == -1:
                trade = self.api.trade(self.symbol, "sell", self.trade_size)
                print(f"SELL executed at {trade['price']}")
            else:
                print("HOLD")

            time.sleep(interval)


# ##########################
# MAIN
# ##########################
if __name__ == "__main__":
    TKEY = "090a47730d2e486a9514e4fb44ba3adf.7fh6qqa7ZgAKLL0ON20dJyskw3E3t-ew3StMe2NmcoRBi4r4TNRcu34Ewc4qEuNK"
    SYMBOL = "TSLA"
    INTERVAL = 20
    TRADE_SIZE = 0.01

    # API client
    traydner = api.TraydnerAPI(api_key=TKEY)

    # Candle builder
    builder = BuildCandles(api_client=traydner, symbol=SYMBOL, interval_sec=INTERVAL)

    # Display
    display = ConsoleDisplay(max_candles=50)

    # Preload history
    builder.preload_history(traydner, SYMBOL, limit=200)

    # Strategy
    strategy = ARIMA(short_window=5, long_window=20)

    # Start bot
    bot = TraderBot(traydner, strategy, builder, SYMBOL, display=display, trade_size=TRADE_SIZE)
    print("TRADING STARTED", time.strftime("%Y-%m-%d %H:%M:%S"))
    bot.run(interval=INTERVAL)
