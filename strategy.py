from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from indicators import ema, rsi, atr, bollinger

@dataclass
class Signal:
    action: str
    confidence: float
    buy_score: float
    sell_score: float
    reason: str
    atr_value: float

def generate_signal(candles: list[list[float]]) -> Signal:
    arr = np.asarray(candles, dtype=float)
    high, low, close, volume = arr[:, 2], arr[:, 3], arr[:, 4], arr[:, 5]

    fast = ema(close, 12)
    slow = ema(close, 26)
    r = rsi(close, 14)
    a = atr(high, low, close, 14)
    lower, middle, upper = bollinger(close, 20)

    buy = 0.0
    sell = 0.0
    reasons: list[str] = []

    if fast[-1] > slow[-1] and fast[-1] > fast[-2]:
        buy += 0.35
        reasons.append("emelkedő trend")
    elif fast[-1] < slow[-1] and fast[-1] < fast[-2]:
        sell += 0.35
        reasons.append("csökkenő trend")

    if 45 <= r[-1] <= 68:
        buy += 0.25
        reasons.append("pozitív momentum")
    elif r[-1] >= 72:
        sell += 0.25
        reasons.append("túlvett állapot")
    elif r[-1] <= 28:
        buy += 0.15
        reasons.append("túladott visszapattanási esély")

    if np.isfinite(lower[-1]) and close[-1] <= lower[-1] * 1.01:
        buy += 0.20
        reasons.append("alsó Bollinger-zóna")
    elif np.isfinite(upper[-1]) and close[-1] >= upper[-1] * 0.99:
        sell += 0.20
        reasons.append("felső Bollinger-zóna")

    vol_mean = float(np.mean(volume[-20:]))
    if volume[-1] > vol_mean * 1.20:
        if close[-1] > close[-2]:
            buy += 0.20
            reasons.append("forgalommal megerősített emelkedés")
        else:
            sell += 0.20
            reasons.append("forgalommal megerősített esés")

    confidence = max(buy, sell)
    if buy > sell:
        action = "BUY"
    elif sell > buy:
        action = "SELL"
    else:
        action = "HOLD"

    return Signal(
        action=action,
        confidence=min(confidence, 1.0),
        buy_score=buy,
        sell_score=sell,
        reason=", ".join(reasons) or "nincs megerősített jel",
        atr_value=float(a[-1]),
    )
