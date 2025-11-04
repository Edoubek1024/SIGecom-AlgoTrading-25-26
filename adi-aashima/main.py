import time
import json
import pandas as pd
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import traydner_lib as td

# === CONFIGURATION ===
SYMBOLS = ["BTC", "ETH", "SOL"]  # add more symbols as needed
MARKET = "crypto"
RESOLUTION = "15m"
EMA_FAST = 9   # fast EMA over 9 periods (≈ 2.25 hours)
EMA_SLOW = 21  # slow EMA over 21 periods (≈ 5.25 hours)
RSI_PERIOD = 14
POLL_INTERVAL = 15*60
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
CAPITAL_FRACTION = 0.1
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
LOG_FILE = "trade_log.jsonl"
MAX_THREADS = 5

# === STATE ===
state = {s: {"position": 0, "entry_price": None, "last_signal": None} for s in SYMBOLS}

def save_state():
    with open("state.json", "w") as f:
        json.dump(state, f)

def load_state():
    global state
    try:
        with open("state.json") as f:
            state.update(json.load(f))
    except FileNotFoundError:
        pass

def log_event(symbol: str, event_type: str, data: dict):
    entry = {"time": datetime.now().isoformat(), "symbol": symbol, "event": event_type, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def fetch_candles(symbol: str, resolution: str, limit: int = 100):
    data = td.symbol_history(symbol, resolution, limit)
    if not data or "history" not in data:
        log_event(symbol, "error", {"msg": "Failed to fetch candles"})
        return None
    df = pd.DataFrame(data["history"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("timestamp", inplace=True)
    return df

def compute_ema(df: pd.DataFrame, span: int):
    return df["close"].ewm(span=span, adjust=False).mean()

def compute_rsi(df: pd.DataFrame, period: int):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal(symbol, df: pd.DataFrame) -> Optional[str]:
    if len(df) < max(EMA_SLOW, RSI_PERIOD):
        return None
    df["ema_fast"] = compute_ema(df, EMA_FAST)
    df["ema_slow"] = compute_ema(df, EMA_SLOW)
    df["rsi"] = compute_rsi(df, RSI_PERIOD)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    print(f"{symbol} | EMA_FAST={last['ema_fast']:.2f} EMA_SLOW={last['ema_slow']:.2f} RSI={last['rsi']:.2f}")

    # Long: EMA fast crosses above EMA slow AND RSI not overbought
    if prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"] and last["rsi"] < RSI_OVERBOUGHT:
        return "buy"
    # Short: EMA fast crosses below EMA slow AND RSI not oversold
    elif prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"] and last["rsi"] > RSI_OVERSOLD:
        return "sell"
    return None

MIN_QTY = 1e-6  # adjust according to API minimum

def qty_from_balance(symbol: str, side: str):
    price_info = td.symbol_price(symbol)
    if not price_info:
        return 0
    price = price_info["price"]
    bal = td.account_balance()
    if not bal:
        return 0

    if side == "buy":
        cash = bal.get("cash", 0)
        qty = (cash * CAPITAL_FRACTION) / price
    elif side == "sell":
        holding = bal.get(MARKET, {}).get(symbol, 0)
        qty = holding  # sell full holding for TP/SL
    else:
        return 0

    if qty < MIN_QTY:
        return 0
    return round(qty, 6)

def check_stops(symbol: str, price: float):
    st = state[symbol]
    if st["position"] == 0 or not st["entry_price"]:
        return
    entry = st["entry_price"]
    change = (price - entry) / entry

    # long position stop/TP
    if st["position"] == 1:
        if change <= -STOP_LOSS_PCT:
            log_event(symbol, "stop_loss_long", {"price": price, "entry": entry})
            qty = qty_from_balance(symbol, "sell")
            if qty > 0:
                td.symbol_trade(symbol, "sell", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})
        elif change >= TAKE_PROFIT_PCT:
            log_event(symbol, "take_profit_long", {"price": price, "entry": entry})
            qty = qty_from_balance(symbol, "sell")
            if qty > 0:
                td.symbol_trade(symbol, "sell", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})

    # short position stop/TP
    elif st["position"] == -1:
        if change >= STOP_LOSS_PCT:
            log_event(symbol, "stop_loss_short", {"price": price, "entry": entry})
            qty = qty_from_balance(symbol, "buy")
            if qty > 0:
                td.symbol_trade(symbol, "buy", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})
        elif change <= -TAKE_PROFIT_PCT:
            log_event(symbol, "take_profit_short", {"price": price, "entry": entry})
            qty = qty_from_balance(symbol, "buy")
            if qty > 0:
                td.symbol_trade(symbol, "buy", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})

def trade_logic(symbol: str):
    st = state[symbol]
    status = td.market_status(MARKET)
    if not status or not status.get("isOpen", True):
        log_event(symbol, "market_closed", {})
        return

    candles = fetch_candles(symbol, RESOLUTION)
    if candles is None:
        log_event(symbol, "no_candles", {})
        return

    price_info = td.symbol_price(symbol)
    if not price_info:
        log_event(symbol, "no_price_info", {})
        return
    price = price_info["price"]

    check_stops(symbol, price)

    signal = get_signal(symbol, candles)
    if signal is None or signal == st["last_signal"]:
        log_event(symbol, "no_signals", {})
        return

    qty = qty_from_balance(symbol, "buy" if signal=="buy" else "sell")
    if qty <= 0:
        log_event(symbol, "invalid_qty", {"qty": qty})
        return

    if signal == "buy" and st["position"] <= 0:
        td.symbol_trade(symbol, "buy", qty)
        st.update({"position": 1, "entry_price": price, "last_signal": signal})
        log_event(symbol, "buy", {"qty": qty, "price": price})
        print(f"{datetime.now()}: BUY {qty} {symbol} at {price:.2f}")
    elif signal == "sell" and st["position"] >= 0:
        td.symbol_trade(symbol, "sell", qty)
        st.update({"position": -1, "entry_price": price, "last_signal": signal})
        log_event(symbol, "sell", {"qty": qty, "price": price})
        print(f"{datetime.now()}: SELL {qty} {symbol} at {price:.2f}")

    save_state()

def main():
    print(f"Starting EMA+RSI Bot on {SYMBOLS} at {RESOLUTION}")
    load_state()
    log_event("system", "start", {"symbols": SYMBOLS, "resolution": RESOLUTION})
    executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
    while True:
        futures = [executor.submit(trade_logic, sym) for sym in SYMBOLS]
        for f in futures:
            f.result()  # wait for completion
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()