import requests
import time
import statistics

API_KEY = "2dc41117bfcc47f8a7dd474052230179.IvPHJ3FAd_mbTMOuE2hZxDP1Q6g1WUVmpEeVUhNfbz9raza-Gn3rECZFjir9Hpvt"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
SYMBOL = "BTC"
RESOLUTION = "1m"
HISTORY_LIMIT = 20
MAX_TRADE_AMOUNT = 50000  # Max USD per trade

# ---------------- Helper functions ----------------
def get_price():
    url = f"https://traydner-186649552655.us-central1.run.app/api/remote/price?symbol={SYMBOL}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    data = r.json()
    price = data.get('price')
    if isinstance(price, (int, float)):
        return float(price)
    if isinstance(price, dict) and 'amount' in price:
        return float(price['amount'])
    raise ValueError(f"Unexpected price data: {data}")

def get_balance():
    url = "https://traydner-186649552655.us-central1.run.app/api/remote/balance"
    r = requests.get(url, headers=HEADERS, timeout=10)
    data = r.json()
    balance_data = data.get('balance')
    if isinstance(balance_data, dict):
        cash = float(balance_data.get('cash', 0))
        btc = float(balance_data.get('crypto', {}).get('BTC', 0))
        return cash, btc
    raise ValueError(f"Unexpected balance data: {data}")

def get_history():
    url = f"https://traydner-186649552655.us-central1.run.app/api/remote/history?symbol={SYMBOL}&resolution={RESOLUTION}&limit={HISTORY_LIMIT}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    data = r.json()
    if isinstance(data.get('history'), list):
        closes = [h['close'] for h in data['history'] if 'close' in h]
        if closes:
            return closes
    raise ValueError(f"Unexpected history data: {data}")

def buy(quantity):
    url = f"https://traydner-186649552655.us-central1.run.app/api/remote/trade?symbol={SYMBOL}&side=buy&quantity={quantity}"
    r = requests.post(url, headers=HEADERS, timeout=20)
    print("BUY:", r.json())

def sell(quantity):
    url = f"https://traydner-186649552655.us-central1.run.app/api/remote/trade?symbol={SYMBOL}&side=sell&quantity={quantity}"
    r = requests.post(url, headers=HEADERS, timeout=20)
    print("SELL:", r.json())

# ---------------- Initialize ----------------
cash_balance, btc_held = get_balance()
current_price = get_price()
starting_worth = cash_balance + btc_held * current_price
print(f"Starting account worth: ${starting_worth:.2f}")

last_action = None

# ---------------- Trading loop ----------------
while True:
    try:
        closes = get_history()
        mean_price = statistics.mean(closes)
        std_dev = statistics.stdev(closes)
        current_price = get_price()
        cash_balance, btc_held = get_balance()

        deviation = current_price - mean_price

        # Dynamic trade sizing
        if deviation < 0:  # buying side
            scale = min(1, max(0.1, abs(deviation) / std_dev))
            trade_amount = MAX_TRADE_AMOUNT * scale
            quantity = trade_amount / current_price
        else:  # selling side
            scale = min(1, max(0.1, deviation / std_dev))
            quantity = btc_held * scale

        # Print profit/loss
        net_worth = cash_balance + btc_held * current_price
        profit = net_worth - starting_worth

        print(f"Price: {current_price:.2f}, Mean: {mean_price:.2f}, Std: {std_dev:.2f}, "
              f"Deviation: {deviation:.2f}, Scale: {scale:.2f}, Cash: {cash_balance:.2f}, BTC: {btc_held:.4f}, "
              f"Qty: {quantity:.4f}, Net worth: ${net_worth:.2f}, Profit: ${profit:.2f}")

        # Buy if price below mean - 0.2 * std_dev
        if current_price < mean_price - 0.2 * std_dev and cash_balance >= trade_amount:
            if last_action != "buy":
                print("Buying BTC (dynamic)")
                buy(quantity)
                last_action = "buy"

        # Sell if price above mean + 0.05 * std_dev
        elif current_price > mean_price + 0.05 * std_dev and btc_held > 0:
            if last_action != "sell":
                print("Selling BTC (dynamic)")
                sell(quantity)
                last_action = "sell"

        time.sleep(10)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
