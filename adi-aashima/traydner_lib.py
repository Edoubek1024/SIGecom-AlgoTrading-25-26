import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://traydner-186649552655.us-central1.run.app/"
API_KEY = os.getenv("API_KEY")

def symbol_price(symbol):
    try:
        response = requests.get(API_BASE + f"api/remote/price?symbol={symbol}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price for symbol {symbol}: {e}")
        return None
    
def symbol_trade(symbol, side, quantity):
    try:
        response = requests.post(API_BASE + f"api/remote/trade?symbol={symbol}&side={side}&quantity={quantity}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error executing trade for symbol {symbol} on side {side} at quantity {quantity}: {e}")
        return None
    
def account_balance():
    try:
        response = requests.get(API_BASE + f"api/remote/balance", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching account balance: {e}")
        return None

def symbol_history(symbol, resolution, limit=500):
    try:
        response = requests.get(API_BASE + f"api/remote/history?symbol={symbol}&resolution={resolution}&limit={limit}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {limit} candles of symbol {symbol} at resolution {resolution}: {e}")
        return None

def market_status(market):
    try:
        response = requests.get(API_BASE + f"api/remote/market_status?market={market}", headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market status: {e}")
        return None
