from __future__ import annotations
import logging
import time

from broker import Broker
from config import Config
from risk import arbitrage_shield, position_size
from strategy import generate_signal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def run():
    cfg = Config()
    broker = Broker(cfg)
    start_equity = cfg.starting_cash

    logging.info(
        "Robot indul | exchange=%s symbol=%s paper=%s sandbox=%s",
        cfg.exchange, cfg.symbol, cfg.paper_mode, cfg.sandbox_mode
    )

    while True:
        try:
            candles, price, bid, ask = broker.fetch_market()
            signal = generate_signal(candles)
            equity = broker.equity(price)

            shield = arbitrage_shield(
                cfg, price, bid, ask, signal.atr_value, start_equity, equity
            )

            pos = broker.position
            logging.info(
                "ár=%.4f equity=%.2f jel=%s bizalom=%.2f buy=%.2f sell=%.2f pajzs=%s ok=%s",
                price, equity, signal.action, signal.confidence,
                signal.buy_score, signal.sell_score,
                shield.reason, shield.allowed,
            )

            if pos.amount > 0:
                if price <= pos.stop_price:
                    logging.warning("STOP aktiválódott.")
                    broker.sell_all(price)
                elif price >= pos.take_profit_price:
                    logging.info("TAKE PROFIT aktiválódott.")
                    broker.sell_all(price)
                elif signal.action == "SELL" and signal.confidence >= cfg.min_confidence:
                    logging.info("Stratégiai SELL.")
                    broker.sell_all(price)

            elif (
                shield.allowed
                and signal.action == "BUY"
                and signal.confidence >= cfg.min_confidence
            ):
                amount = position_size(cfg, broker.cash, price, signal.atr_value)
                stop = price - signal.atr_value * cfg.stop_atr_multiplier
                risk_per_unit = price - stop
                take_profit = price + risk_per_unit * cfg.take_profit_r
                broker.buy(amount, price, stop, take_profit)
                logging.info(
                    "BUY | amount=%.8f entry=%.4f stop=%.4f tp=%.4f | %s",
                    amount, price, stop, take_profit, signal.reason
                )

        except KeyboardInterrupt:
            logging.info("Leállítás felhasználói kérésre.")
            break
        except Exception as exc:
            logging.exception("Ciklus hiba: %s", exc)

        time.sleep(cfg.loop_seconds)

if __name__ == "__main__":
    run()
