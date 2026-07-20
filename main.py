from __future__ import annotations
import logging
import time

import numpy as np

from broker import Broker
from config import Config
from dollar_proxy_thermometer import DollarProxyCache
from risk import arbitrage_shield, position_size
from strategy import generate_signal
from xau_model import MarketState, XauFundamentals, assess_xau

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def build_market_state(candles: list[list[float]], bid: float, ask: float) -> MarketState:
    arr = np.asarray(candles, dtype=float)
    close = arr[:, 4]
    volume = arr[:, 5]
    recent_return = (close[-1] / close[-2] - 1.0) if close[-2] else 0.0
    momentum = (close[-1] / close[-6] - 1.0) if len(close) >= 6 and close[-6] else recent_return
    vol_mean = float(np.mean(volume[-20:])) if len(volume) >= 20 else float(np.mean(volume))
    volume_signal = 0.0 if vol_mean <= 0 else max(-1.0, min(1.0, volume[-1] / vol_mean - 1.0))
    mid = (bid + ask) / 2.0
    spread_pct = 0.0 if mid <= 0 else (ask - bid) / mid
    liquidity_signal = max(-1.0, min(1.0, 1.0 - spread_pct / 0.005))
    return MarketState(
        return_signal=max(-1.0, min(1.0, recent_return * 100.0)),
        momentum=max(-1.0, min(1.0, momentum * 50.0)),
        volume_signal=volume_signal,
        liquidity_signal=liquidity_signal,
    )


def run():
    cfg = Config()
    broker = Broker(cfg)
    start_equity = cfg.starting_cash
    dollar_proxy_cache = DollarProxyCache(ttl_seconds=cfg.dollar_proxy_ttl_seconds)

    logging.info(
        "Robot indul | exchange=%s symbol=%s paper=%s sandbox=%s xau_model=%s dollar_proxy=%s",
        cfg.exchange,
        cfg.symbol,
        cfg.paper_mode,
        cfg.sandbox_mode,
        cfg.enable_xau_model,
        cfg.enable_dollar_proxy,
    )

    while True:
        try:
            candles, price, bid, ask = broker.fetch_market()
            signal = generate_signal(candles)
            equity = broker.equity(price)

            shield = arbitrage_shield(
                cfg, price, bid, ask, signal.atr_value, start_equity, equity
            )

            xau_gate = "ALLOW"
            xau_multiplier = 1.0
            if cfg.enable_xau_model:
                fundamentals = XauFundamentals(
                    dxy_change=cfg.dxy_change,
                    real_yield_change=cfg.real_yield_change,
                    geopolitical_risk=cfg.geopolitical_risk,
                    central_bank_flow=cfg.central_bank_flow,
                    etf_flow=cfg.etf_flow,
                    physical_balance=cfg.physical_balance,
                )
                market_state = build_market_state(candles, bid, ask)
                forward = cfg.xau_forward_price if cfg.xau_forward_price > 0 else price
                assessment = assess_xau(
                    fundamentals=fundamentals,
                    market=market_state,
                    spot=price,
                    forward=forward,
                    years=cfg.xau_term_years,
                    rate=cfg.risk_free_rate,
                    storage=cfg.storage_rate,
                    convenience_yield=cfg.convenience_yield,
                    residual_mean=cfg.residual_mean,
                    residual_std=cfg.residual_std,
                    basis_mean=cfg.basis_mean,
                    basis_std=cfg.basis_std,
                )
                xau_gate = assessment.gate
                xau_multiplier = assessment.position_multiplier
                logging.info(
                    "XAU modell | fair=%.4f fund=%.3f angle=%.1f residual_z=%.2f basis_z=%.2f anomaly=%.2f gate=%s label=%s",
                    assessment.fair_value,
                    assessment.fundamental_score,
                    assessment.divergence_angle_deg,
                    assessment.residual_z,
                    assessment.basis_z,
                    assessment.anomaly_score,
                    assessment.gate,
                    assessment.label,
                )

            proxy_gate = "ALLOW"
            proxy_multiplier = 1.0
            if cfg.enable_dollar_proxy:
                try:
                    proxy = dollar_proxy_cache.get(
                        timeout=cfg.dollar_proxy_timeout_seconds,
                        stale_after_days=cfg.dollar_proxy_stale_days,
                    )
                    proxy_gate = proxy.gate
                    proxy_multiplier = proxy.position_multiplier
                    logging.info(
                        "$Proxy Hőmérő | score=%.1f state=%s gate=%s stale=%s broad=%.3f(%s) real10y=%.3f(%s) vix=%.2f(%s)",
                        proxy.score,
                        proxy.state,
                        proxy.gate,
                        proxy.stale,
                        proxy.broad_dollar.value,
                        proxy.broad_dollar.date,
                        proxy.real_yield_10y.value,
                        proxy.real_yield_10y.date,
                        proxy.vix.value,
                        proxy.vix.date,
                    )
                except Exception as proxy_exc:
                    logging.exception("$Proxy adatforrás hiba: %s", proxy_exc)
                    if cfg.dollar_proxy_fail_closed:
                        proxy_gate = "BLOCK"
                        proxy_multiplier = 0.0

            pos = broker.position
            logging.info(
                "ár=%.4f equity=%.2f jel=%s bizalom=%.2f buy=%.2f sell=%.2f pajzs=%s ok=%s proxy=%s",
                price,
                equity,
                signal.action,
                signal.confidence,
                signal.buy_score,
                signal.sell_score,
                shield.reason,
                shield.allowed,
                proxy_gate,
            )

            if pos.amount > 0:
                if price <= pos.stop_price:
                    logging.warning("STOP aktiválódott.")
                    broker.sell_all(price)
                elif price >= pos.take_profit_price:
                    logging.info("TAKE PROFIT aktiválódott.")
                    broker.sell_all(price)
                elif xau_gate == "BLOCK":
                    logging.warning("XAU anomáliakapu BLOCK: pozíció zárása.")
                    broker.sell_all(price)
                elif signal.action == "SELL" and signal.confidence >= cfg.min_confidence:
                    logging.info("Stratégiai SELL.")
                    broker.sell_all(price)

            elif (
                shield.allowed
                and xau_gate != "BLOCK"
                and proxy_gate != "BLOCK"
                and signal.action == "BUY"
                and signal.confidence >= cfg.min_confidence
            ):
                combined_multiplier = min(xau_multiplier, proxy_multiplier)
                amount = position_size(cfg, broker.cash, price, signal.atr_value) * combined_multiplier
                stop = price - signal.atr_value * cfg.stop_atr_multiplier
                risk_per_unit = price - stop
                take_profit = price + risk_per_unit * cfg.take_profit_r
                broker.buy(amount, price, stop, take_profit)
                logging.info(
                    "BUY | amount=%.8f entry=%.4f stop=%.4f tp=%.4f xau_gate=%s proxy_gate=%s | %s",
                    amount,
                    price,
                    stop,
                    take_profit,
                    xau_gate,
                    proxy_gate,
                    signal.reason,
                )

        except KeyboardInterrupt:
            logging.info("Leállítás felhasználói kérésre.")
            break
        except Exception as exc:
            logging.exception("Ciklus hiba: %s", exc)

        time.sleep(cfg.loop_seconds)


if __name__ == "__main__":
    run()
