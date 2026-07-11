from __future__ import annotations
from dataclasses import dataclass
from math import acos, exp, log, sqrt
from typing import Iterable


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_z(value: float, mean: float, std: float) -> float:
    return 0.0 if std <= 1e-12 else (value - mean) / std


@dataclass(frozen=True)
class XauFundamentals:
    dxy_change: float = 0.0
    real_yield_change: float = 0.0
    geopolitical_risk: float = 0.0
    central_bank_flow: float = 0.0
    etf_flow: float = 0.0
    physical_balance: float = 0.0


@dataclass(frozen=True)
class MarketState:
    return_signal: float
    momentum: float
    volume_signal: float
    liquidity_signal: float


@dataclass(frozen=True)
class XauAssessment:
    fundamental_score: float
    divergence_angle_deg: float
    fair_value: float
    residual_z: float
    basis_z: float
    anomaly_score: float
    gate: str
    position_multiplier: float
    label: str


DEFAULT_WEIGHTS = {
    "dxy_change": -0.24,
    "real_yield_change": -0.28,
    "geopolitical_risk": 0.16,
    "central_bank_flow": 0.14,
    "etf_flow": 0.10,
    "physical_balance": 0.08,
}


def fundamental_score(f: XauFundamentals, weights: dict[str, float] | None = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    score = sum(getattr(f, key) * weight for key, weight in w.items())
    return clamp(score, -1.0, 1.0)


def divergence_angle(fundamental_vector: Iterable[float], market_vector: Iterable[float]) -> float:
    f = list(fundamental_vector)
    m = list(market_vector)
    if len(f) != len(m) or not f:
        raise ValueError("A vektoroknak azonos, nem nulla hosszúságúnak kell lenniük.")
    dot = sum(a * b for a, b in zip(f, m))
    nf = sqrt(sum(a * a for a in f))
    nm = sqrt(sum(b * b for b in m))
    if nf <= 1e-12 or nm <= 1e-12:
        return 90.0
    cosine = clamp(dot / (nf * nm), -1.0, 1.0)
    return acos(cosine) * 180.0 / 3.141592653589793


def cost_of_carry_fair_value(spot: float, rate: float, storage: float, convenience_yield: float, years: float) -> float:
    if spot <= 0 or years < 0:
        raise ValueError("Érvénytelen spot ár vagy futamidő.")
    return spot * exp((rate + storage - convenience_yield) * years)


def implied_term_years(spot: float, forward: float, rate: float, storage: float, convenience_yield: float) -> float | None:
    drift = rate + storage - convenience_yield
    if spot <= 0 or forward <= 0 or abs(drift) <= 1e-12:
        return None
    return log(forward / spot) / drift


def assess_xau(
    fundamentals: XauFundamentals,
    market: MarketState,
    spot: float,
    forward: float,
    years: float,
    rate: float,
    storage: float,
    convenience_yield: float,
    residual_mean: float = 0.0,
    residual_std: float = 1.0,
    basis_mean: float = 0.0,
    basis_std: float = 1.0,
) -> XauAssessment:
    score = fundamental_score(fundamentals)
    fvec = [
        -fundamentals.dxy_change,
        -fundamentals.real_yield_change,
        fundamentals.geopolitical_risk,
        fundamentals.central_bank_flow,
    ]
    mvec = [market.return_signal, market.momentum, market.volume_signal, market.liquidity_signal]
    angle = divergence_angle(fvec, mvec)

    fair = cost_of_carry_fair_value(spot, rate, storage, convenience_yield, years)
    residual = spot - fair
    residual_z_value = safe_z(residual, residual_mean, residual_std)
    basis = forward - fair
    basis_z_value = safe_z(basis, basis_mean, basis_std)

    angle_score = clamp(angle / 90.0, 0.0, 1.0)
    residual_score = clamp(abs(residual_z_value) / 3.0, 0.0, 1.0)
    basis_score = clamp(abs(basis_z_value) / 3.0, 0.0, 1.0)
    liquidity_risk = clamp(-market.liquidity_signal, 0.0, 1.0)
    anomaly = clamp(
        angle_score * 0.35 + residual_score * 0.30 + basis_score * 0.20 + liquidity_risk * 0.15,
        0.0,
        1.0,
    )

    if anomaly >= 0.75 or abs(residual_z_value) >= 3.0:
        gate, multiplier, label = "BLOCK", 0.0, "MAGAS ANOMÁLIAKOCKÁZAT"
    elif anomaly >= 0.45 or angle >= 45.0 or abs(residual_z_value) >= 2.0:
        gate, multiplier, label = "REDUCE", 0.35, "FUNDAMENTÁLIS DIVERGENCIA"
    else:
        gate, multiplier, label = "ALLOW", 1.0, "NORMÁL MOZGÁS"

    return XauAssessment(
        fundamental_score=score,
        divergence_angle_deg=angle,
        fair_value=fair,
        residual_z=residual_z_value,
        basis_z=basis_z_value,
        anomaly_score=anomaly,
        gate=gate,
        position_multiplier=multiplier,
        label=label,
    )
