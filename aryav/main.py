import api
import time
from log import log
import numpy as np
from dotenv import dotenv_values

KEY = dotenv_values('.env')['KEY']
TRADE_PERCENTAGE = 1

class Trader:
    MAX_HISTORY = 30
    
    def __init__(self, key, target, market):
        self.api = api.TraydnerAPI(key)
        self.price_history = []
        self.balance = self.api.get_balance()['balance']
        self.entry_price = -1
        self.portfolio = {}
        if self.balance is not float:
            self.portfolio['crypto'] = self.balance['crypto']
            self.portfolio['stocks']= self.balance['stocks']
            self.portfolio['forex'] = self.balance['forex']
            self.balance = self.balance['cash']
        self.target = target
        self.market = market
    
    def _refresh(self):
        self.balance = self.api.get_balance()['balance']
        self.portfolio = {}
        if self.balance is not float:
            self.portfolio['crypto'] = self.balance['crypto']
            self.portfolio['stocks']= self.balance['stocks']
            self.portfolio['forex'] = self.balance['forex']
            self.balance = self.balance['cash']
    
    def add_history(self, price):
        if len(self.price_history) > self.MAX_HISTORY:
            self.price_history.pop(0)
        self.price_history.append(price)
        
    def buy_signal(self):
        if len(self.price_history) < 15:
            log("not enough data to compute buy signal", level="WARNING")
            return False
        
        short_avg = np.mean(self.price_history[-5:])
        long_avg = np.mean(self.price_history[-15:])
        return short_avg > long_avg
    
    def get_units(self):
        return self.balance * TRADE_PERCENTAGE / self.price_history[-1]
    
    def buy(self):
        units = self.get_units()
        self.api.make_trade(self.target, "buy", units)
        self.entry_price = self.price_history[-1]
        self._refresh()
        log(f"buy: {self.target} at {units * self.entry_price} (balance: {self.balance})", level="WARNING")
    
    def holding(self):
        return self.market in self.portfolio and self.target in self.portfolio[self.market]
    
    def sell(self):
        if self.market not in self.portfolio or self.target not in self.portfolio[self.market]:
            log(f"sell {self.target} not possible", level="WARNING")
            return
        
        units = self.portfolio[self.market][self.target]
        self.api.make_trade(self.target, 'sell', units)
        self._refresh()
        log(f"sell: {self.target} at {units * self.entry_price} (balance: {self.balance})", level="WARNING")
        self.entry_price = -1
        

trader = Trader(KEY, "btc", "crypto")
trading_loop = True

log("init ok")
log(f"Balance: {trader.balance}")

cp_count = 4

while trading_loop:
    if len(trader.price_history) < 15:
        current_price = trader.api.get_price(trader.target)['price']
        trader.add_history(current_price)
        log(f"collecting data... [{len(trader.price_history)}]")
        time.sleep(1)
        continue

    current_price = trader.api.get_price(trader.target)['price']
    trader.add_history(current_price)
    cp_count += 1
    
    if cp_count % 5 == 0: 
        log(f"cp {current_price}")
        if trader.holding(): 
            log(f"% {100 * (current_price - trader.entry_price)/trader.entry_price}")
        cp_count = 0
        
    buy_signal = trader.buy_signal()
    
    if trader.holding():
        if current_price > trader.entry_price * 1.002 or current_price < trader.entry_price * 0.999:
            trader.sell()
    
    if buy_signal and not trader.holding():
        trader.buy()
    
    time.sleep(1)

