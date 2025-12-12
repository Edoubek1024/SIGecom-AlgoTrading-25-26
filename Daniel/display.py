import time
import os
from colorama import init, Fore, Style

init(autoreset=True)

class ConsoleDisplay:
    def __init__(self, max_candles=20, height=10):
        self.candles = []      
        self.trades = []       
        self.history = []      
        self.history_trades = []  
        self.max_candles = max_candles
        self.height = height

    def add_candle(self, candle):
        self.history.append(candle)
        self.candles.append(candle)
        print("Candle added to builder:", candle)
        if len(self.candles) > self.max_candles:
            self.candles.pop(0)

    def add_trade(self, index, side):
        trade = {"index": index, "side": side}
        self.history_trades.append(trade)
        if index >= len(self.history) - self.max_candles:
            display_index = index - (len(self.history) - self.max_candles)
            self.trades.append({"index": display_index, "side": side})

    def _get_scaled_heights(self):
        closes = [c["close"] for c in self.candles]
        highs = [c["high"] for c in self.candles]
        lows = [c["low"] for c in self.candles]
        max_price = max(highs)
        min_price = min(lows)
        scale = max_price - min_price if max_price != min_price else 1

        heights = []
        for c in self.candles:
            open_row = int((c["open"] - min_price) / scale * (self.height - 1))
            close_row = int((c["close"] - min_price) / scale * (self.height - 1))
            high_row = int((c["high"] - min_price) / scale * (self.height - 1))
            low_row = int((c["low"] - min_price) / scale * (self.height - 1))
            heights.append({
                "open_row": open_row,
                "close_row": close_row,
                "high_row": high_row,
                "low_row": low_row,
                "color": Fore.GREEN if c["close"] > c["open"] else Fore.RED if c["close"] < c["open"] else Fore.YELLOW
            })
        return heights

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')

        heights = self._get_scaled_heights()
        rows = [[" "]*len(heights) for _ in range(self.height)]

        for col, h in enumerate(heights):
            top = max(h["open_row"], h["close_row"])
            bottom = min(h["open_row"], h["close_row"])
            for row in range(bottom, top+1):
                rows[self.height - 1 - row][col] = h["color"] + "█" + Style.RESET_ALL
            for row in range(top+1, h["high_row"]+1):
                rows[self.height - 1 - row][col] = h["color"] + "│" + Style.RESET_ALL
            for row in range(h["low_row"], bottom):
                rows[self.height - 1 - row][col] = h["color"] + "│" + Style.RESET_ALL

        for t in self.trades:
            if 0 <= t["index"] < len(heights):
                col = t["index"]
                rows[0][col] = Fore.CYAN + ("B" if t["side"]=="buy" else "S") + Style.RESET_ALL

        for row in rows:
            print("".join(row))

        closes = [str(c["close"]) for c in self.candles]
        print("Closes:", " ".join(closes))
        print("-"*40)

'''if __name__ == "__main__":
    display = ConsoleDisplay(max_candles=20, height=10)

    for i in range(40):  # longer history than window
        candle = {
            "open": 100+i,
            "high": 100+i+3,
            "low": 100+i-2,
            "close": 100+i+1 if i%2==0 else 100+i-1
        }
        display.add_candle(candle)

        if i % 5 == 0:
            display.add_trade(index=i, side="buy" if i%10==0 else "sell")

        display.render()
        time.sleep(0.1)

    for i, candle in enumerate(display.history):
        trades_here = [t for t in display.history_trades if t['index'] == i]
        print(f"Candle {i}: Close={candle['close']}, Trades: {[t['side'] for t in trades_here]}")
'''
