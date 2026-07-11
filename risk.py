from dataclasses import dataclass
from config import Config

@dataclass
class ShieldDecision:
    allowed: bool
    reason: str

def arbitrage_shield(
    cfg: Config,
    price: float,
    bid: float,
    ask: float,
    atr_value: float,
    start_equity: float,
    current_equity: float,
) -> ShieldDecision:
    if price <= 0 or bid <= 0 or ask <= 0:
        return ShieldDecision(False, "hibás piaci ár")

    spread_pct = (ask - bid) / price
    if spread_pct > cfg.max_spread_pct:
        return ShieldDecision(False, f"túl nagy spread: {spread_pct:.3%}")

    atr_pct = atr_value / price
    if atr_pct > cfg.max_atr_pct:
        return ShieldDecision(False, f"extrém volatilitás: ATR {atr_pct:.3%}")

    drawdown = (start_equity - current_equity) / max(start_equity, 1e-12)
    if drawdown >= cfg.max_daily_loss:
        return ShieldDecision(False, f"napi veszteséglimit elérve: {drawdown:.2%}")

    return ShieldDecision(True, "pajzs engedélyezte")

def position_size(cfg: Config, cash: float, price: float, atr_value: float) -> float:
    stop_distance = max(atr_value * cfg.stop_atr_multiplier, price * 0.002)
    risk_budget = cash * cfg.risk_per_trade
    by_risk = risk_budget / stop_distance
    by_cap = (cash * cfg.max_position_fraction) / price
    return max(0.0, min(by_risk, by_cap))
