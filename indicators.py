from __future__ import annotations
import numpy as np

def ema(values: np.ndarray, period: int) -> np.ndarray:
    if len(values) < period:
        raise ValueError("Nincs elegendő adat az EMA számításához.")
    alpha = 2.0 / (period + 1.0)
    out = np.empty_like(values, dtype=float)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out

def rsi(values: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(values, prepend=values[0])
    gains = np.maximum(delta, 0.0)
    losses = np.maximum(-delta, 0.0)
    avg_gain = ema(gains, period)
    avg_loss = ema(losses, period)
    rs = avg_gain / np.where(avg_loss == 0, 1e-12, avg_loss)
    return 100.0 - (100.0 / (1.0 + rs))

def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum.reduce([
        high - low,
        np.abs(high - prev_close),
        np.abs(low - prev_close),
    ])
    return ema(tr, period)

def bollinger(values: np.ndarray, period: int = 20, std_mult: float = 2.0):
    middle = np.full_like(values, np.nan, dtype=float)
    upper = np.full_like(values, np.nan, dtype=float)
    lower = np.full_like(values, np.nan, dtype=float)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        mean = float(np.mean(window))
        std = float(np.std(window))
        middle[i] = mean
        upper[i] = mean + std_mult * std
        lower[i] = mean - std_mult * std
    return lower, middle, upper
