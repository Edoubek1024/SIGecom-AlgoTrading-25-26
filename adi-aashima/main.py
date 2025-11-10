import time
import json
import pandas as pd
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import traydner_lib as td

# === MARKET CONFIG ===
SYMBOLS = ["BTC", "ETH", "SOL"]
MARKET = "crypto"
RESOLUTION = "15m"

# === WINDOW CONFIG ===
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Time between trades
POLL_INTERVAL = 15 * 60
# Max cash to use on a single trade
CAPITAL_FRACTION = 0.1
# How much to lose/profit before selling
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
# Minimum fraction of symbol to buy
MIN_QTY = 1e-6

MAX_THREADS = 5

LOG_FILE = "./adi-aashima/trade_log.jsonl"
STATE_FILE = "./adi-aashima/state.json"

# === STATE ===
state = {s: {"position": 0, "entry_price": None, "last_signal": None} for s in SYMBOLS}

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    global state
    try:
        with open(STATE_FILE) as f:
            state.update(json.load(f))
    except FileNotFoundError:
        pass

def log_event(symbol: str, event_type: str, data: dict):
    entry = {"time": datetime.now().isoformat(), "symbol": symbol, "event": event_type, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def fetch_candles(symbol: str, resolution: str, limit: int = 500):
    data = td.symbol_history(symbol, resolution, limit)
    if not data or "history" not in data:
        log_event(symbol, "error", {"msg": "Failed to fetch candles", "returned": bool(data)})
        return None
    df = pd.DataFrame(data["history"])
    if "timestamp" not in df.columns or "close" not in df.columns:
        log_event(symbol, "error", {"msg": "missing cols", "cols": df.columns.tolist()})
        return None
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("timestamp", inplace=True)
    # CRITICAL: ensure chronological ascending order
    df.sort_index(inplace=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df

def compute_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def compute_rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal(symbol: str, df: pd.DataFrame, enter_on_trend: bool = True) -> Optional[str]:
    df = df.copy()
    if len(df) < max(EMA_SLOW, RSI_PERIOD) + 1:
        log_event(symbol, "insufficient_history", {"have": len(df), "need": max(EMA_SLOW, RSI_PERIOD) + 1})
        return None

    df["ema_fast"] = compute_ema(df["close"], EMA_FAST)
    df["ema_slow"] = compute_ema(df["close"], EMA_SLOW)
    df["rsi"] = compute_rsi(df["close"], RSI_PERIOD)

    prev = df.iloc[-2]
    last = df.iloc[-1]

    if pd.isna(prev["ema_fast"]) or pd.isna(prev["ema_slow"]) or pd.isna(last["ema_fast"]) or pd.isna(last["ema_slow"]) or pd.isna(last["rsi"]):
        log_event(symbol, "nan_in_indicators", {
            "prev_ema_fast": prev.get("ema_fast"),
            "prev_ema_slow": prev.get("ema_slow"),
            "last_ema_fast": last.get("ema_fast"),
            "last_ema_slow": last.get("ema_slow"),
            "last_rsi": last.get("rsi")
        })
        return None

    log_event(symbol, "indicators", {
        "time": str(last.name),
        "prev_ema_fast": float(prev["ema_fast"]),
        "prev_ema_slow": float(prev["ema_slow"]),
        "last_ema_fast": float(last["ema_fast"]),
        "last_ema_slow": float(last["ema_slow"]),
        "last_rsi": float(last["rsi"])
    })

    # CROSS signals (higher confidence)
    if prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"] and last["rsi"] < RSI_OVERBOUGHT:
        return "buy"
    if prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"] and last["rsi"] > RSI_OVERBOUGHT:
        return "sell"

    # TREND entry (lower confidence). Enter if already in desired state
    if enter_on_trend:
        if last["ema_fast"] > last["ema_slow"] and last["rsi"] < RSI_OVERBOUGHT:
            return "buy"
        if last["ema_fast"] < last["ema_slow"] and last["rsi"] > RSI_OVERBOUGHT:
            return "sell"

    return None

def qty_from_balance(symbol: str, side: str):
    price_info = td.symbol_price(symbol)
    if not price_info:
        log_event(symbol, "no_price_info_for_qty", {})
        return 0.0
    price = price_info.get("price") or price_info.get("last") or price_info.get("last_price") or price_info.get("close")
    try:
        price = float(price)
    except Exception:
        log_event(symbol, "price_parse_error", {"price_info": price_info})
        return 0.0

    bal: dict = td.account_balance().get("balance")
    if not bal:
        log_event(symbol, "no_balance_info", {})
        return 0.0

    if side == "buy":
        cash = bal.get("cash")
        qty = (cash * CAPITAL_FRACTION) / price if price > 0 else 0.0
    else:  # sell
        holding = 0.0
        market_holdings = bal.get(MARKET)
        if isinstance(market_holdings, dict):
            holding = float(market_holdings.get(symbol, 0) or 0)
        else:
            holding = float(bal.get(symbol, 0) or 0)
        qty = holding

    if qty < MIN_QTY:
        log_event(symbol, "qty_too_small", {"side": side, "calculated_qty": float(qty), "min_qty": MIN_QTY, "price": price, "cash": cash})
        return 0.0
    return float(qty)

def check_stops(symbol: str, price: float):
    st = state[symbol]
    if st["position"] == 0 or not st["entry_price"]:
        return
    entry = st["entry_price"]
    change = (price - entry) / entry
    if st["position"] == 1:
        if change <= -STOP_LOSS_PCT:
            log_event(symbol, "stop_loss_long", {"price": price, "entry": entry, "change": change})
            qty = qty_from_balance(symbol, "sell")
            if qty > 0:
                td.symbol_trade(symbol, "sell", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})
        elif change >= TAKE_PROFIT_PCT:
            log_event(symbol, "take_profit_long", {"price": price, "entry": entry, "change": change})
            qty = qty_from_balance(symbol, "sell")
            if qty > 0:
                td.symbol_trade(symbol, "sell", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})
    elif st["position"] == -1:
        if change >= STOP_LOSS_PCT:
            log_event(symbol, "stop_loss_short", {"price": price, "entry": entry, "change": change})
            qty = qty_from_balance(symbol, "buy")
            if qty > 0:
                td.symbol_trade(symbol, "buy", qty)
            st.update({"position": 0, "entry_price": None, "last_signal": None})
        elif change <= -TAKE_PROFIT_PCT:
            log_event(symbol, "take_profit_short", {"price": price, "entry": entry, "change": change})
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
    price = price_info.get("price") or price_info.get("last") or price_info.get("last_price") or price_info.get("close")
    try:
        price = float(price)
    except Exception:
        log_event(symbol, "price_parse_error", {"price_info": price_info})
        return

    check_stops(symbol, price)

    signal = get_signal(symbol, candles)
    if signal is None or signal == st["last_signal"]:
        log_event(symbol, "no_new_signals", {"last_signal": st["last_signal"], "signal": signal})
        return

    side_for_qty = "buy" if signal == "buy" else "sell"
    qty = qty_from_balance(symbol, side_for_qty)
    if qty <= 0:
        log_event(symbol, "invalid_qty", {"qty": qty, "side": side_for_qty})
        return

    if signal == "buy" and st["position"] <= 0:
        td.symbol_trade(symbol, "buy", qty)
        st.update({"position": 1, "entry_price": price, "last_signal": signal})
        log_event(symbol, "buy", {"qty": qty, "price": price})
    elif signal == "sell" and st["position"] >= 0:
        td.symbol_trade(symbol, "sell", qty)
        st.update({"position": -1, "entry_price": price, "last_signal": signal})
        log_event(symbol, "sell", {"qty": qty, "price": price})

    save_state()

def main():
    print(f"Starting EMA+RSI Bot on {SYMBOLS} at {RESOLUTION}")
    load_state()
    log_event("system", "start", {"symbols": SYMBOLS, "resolution": RESOLUTION})
    executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
    while True:
        futures = [executor.submit(trade_logic, sym) for sym in SYMBOLS]
        for f in futures:
            f.result()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()