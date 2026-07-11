from __future__ import annotations
from dataclasses import dataclass
import ccxt
from config import Config

@dataclass
class Position:
    amount: float = 0.0
    entry_price: float = 0.0
    stop_price: float = 0.0
    take_profit_price: float = 0.0

class Broker:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        exchange_cls = getattr(ccxt, cfg.exchange)
        self.exchange = exchange_cls({
            "apiKey": cfg.api_key,
            "secret": cfg.api_secret,
            "enableRateLimit": True,
        })
        if cfg.sandbox_mode:
            self.exchange.set_sandbox_mode(True)

        self.cash = cfg.starting_cash
        self.position = Position()

    def fetch_market(self):
        candles = self.exchange.fetch_ohlcv(
            self.cfg.symbol,
            timeframe=self.cfg.timeframe,
            limit=self.cfg.candle_limit,
        )
        ticker = self.exchange.fetch_ticker(self.cfg.symbol)
        price = float(ticker.get("last") or candles[-1][4])
        bid = float(ticker.get("bid") or price)
        ask = float(ticker.get("ask") or price)
        return candles, price, bid, ask

    def equity(self, mark_price: float) -> float:
        return self.cash + self.position.amount * mark_price

    def buy(self, amount: float, price: float, stop_price: float, take_profit_price: float):
        if amount <= 0:
            return
        if self.cfg.paper_mode:
            cost = amount * price
            fee = cost * self.cfg.fee_rate
            if cost + fee > self.cash:
                raise RuntimeError("Nincs elegendő paper egyenleg.")
            self.cash -= cost + fee
        else:
            self.exchange.create_order(self.cfg.symbol, "market", "buy", amount)

        self.position = Position(amount, price, stop_price, take_profit_price)

    def sell_all(self, price: float):
        amount = self.position.amount
        if amount <= 0:
            return
        if self.cfg.paper_mode:
            proceeds = amount * price
            fee = proceeds * self.cfg.fee_rate
            self.cash += proceeds - fee
        else:
            self.exchange.create_order(self.cfg.symbol, "market", "sell", amount)
        self.position = Position()
