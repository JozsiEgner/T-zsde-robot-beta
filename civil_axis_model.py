from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class CountryResourceInput:
    """Egy ország referencia-termékének és tartalékainak bemenetei.

    Minden pénzértéket ugyanabban a devizában kell megadni.
    A szén-monoxid kockázat normalizált 0..1 érték:
    0 = nincs büntetés, 1 = teljes értékvesztés.
    """

    country: str
    reference_product: str
    annual_quantity: float
    wholesale_price: float
    country_population: float
    strategic_reserve_value: float = 0.0
    market_cap: float = 0.0
    exchange_turnover: float = 0.0
    open_interest: float = 0.0
    production_capacity_score: float = 1.0
    co_risk: float = 0.0


@dataclass(frozen=True)
class GoldReferenceInput:
    above_ground_quantity: float
    spot_price: float
    world_population: float


@dataclass(frozen=True)
class CountryAssessment:
    country: str
    reference_product: str
    product_value: float
    product_value_per_world_capita: float
    reserve_value_per_country_capita: float
    market_support_value: float
    raw_country_value: float
    environmental_multiplier: float
    corrected_country_value: float
    gold_value_per_world_capita: float
    gold_relative_index: float
    classification: str


def _require_non_negative(name: str, value: float) -> float:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} csak véges, nem negatív szám lehet")
    return value


def _require_positive(name: str, value: float) -> float:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} csak véges, pozitív szám lehet")
    return value


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def gold_value_per_world_capita(gold: GoldReferenceInput) -> float:
    quantity = _require_non_negative("above_ground_quantity", gold.above_ground_quantity)
    price = _require_non_negative("spot_price", gold.spot_price)
    population = _require_positive("world_population", gold.world_population)
    return quantity * price / population


def assess_country(
    resource: CountryResourceInput,
    gold: GoldReferenceInput,
    *,
    production_weight: float = 0.60,
    reserve_weight: float = 0.25,
    market_weight: float = 0.15,
) -> CountryAssessment:
    """Kiszámítja az ország aranyhoz viszonyított Civil Axis értékét.

    A súlyok összege 1 kell legyen. A modell három réteget egyesít:
    termelési érték, országon belüli tartalék/fő és piaci támogatás.
    """

    weights = (production_weight, reserve_weight, market_weight)
    if any(not isfinite(weight) or weight < 0 for weight in weights):
        raise ValueError("A súlyok nem lehetnek negatívak")
    if abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError("A súlyok összegének 1-nek kell lennie")

    quantity = _require_non_negative("annual_quantity", resource.annual_quantity)
    wholesale_price = _require_non_negative("wholesale_price", resource.wholesale_price)
    country_population = _require_positive("country_population", resource.country_population)
    world_population = _require_positive("world_population", gold.world_population)
    reserve_value = _require_non_negative("strategic_reserve_value", resource.strategic_reserve_value)
    market_cap = _require_non_negative("market_cap", resource.market_cap)
    turnover = _require_non_negative("exchange_turnover", resource.exchange_turnover)
    open_interest = _require_non_negative("open_interest", resource.open_interest)
    capacity = _require_non_negative("production_capacity_score", resource.production_capacity_score)
    co_risk = clamp(_require_non_negative("co_risk", resource.co_risk), 0.0, 1.0)

    product_value = quantity * wholesale_price
    product_per_world_capita = product_value / world_population
    reserve_per_country_capita = reserve_value / country_population

    # A piaci réteg kiegyenlítetten veszi figyelembe a kapitalizációt,
    # forgalmat és nyitott kötésállományt, majd országonként egy főre vetíti.
    market_support_value = (market_cap + turnover + open_interest) / (3.0 * country_population)

    production_component = product_per_world_capita * capacity
    raw_country_value = (
        production_component * production_weight
        + reserve_per_country_capita * reserve_weight
        + market_support_value * market_weight
    )

    environmental_multiplier = 1.0 - co_risk
    corrected_country_value = raw_country_value * environmental_multiplier
    gold_per_capita = gold_value_per_world_capita(gold)
    relative_index = 0.0 if gold_per_capita == 0 else corrected_country_value / gold_per_capita

    if relative_index >= 1.0:
        classification = "ARANY-SZINT FELETT"
    elif relative_index >= 0.50:
        classification = "ERŐS"
    elif relative_index >= 0.20:
        classification = "KÖZEPES"
    else:
        classification = "GYENGE"

    return CountryAssessment(
        country=resource.country,
        reference_product=resource.reference_product,
        product_value=product_value,
        product_value_per_world_capita=product_per_world_capita,
        reserve_value_per_country_capita=reserve_per_country_capita,
        market_support_value=market_support_value,
        raw_country_value=raw_country_value,
        environmental_multiplier=environmental_multiplier,
        corrected_country_value=corrected_country_value,
        gold_value_per_world_capita=gold_per_capita,
        gold_relative_index=relative_index,
        classification=classification,
    )


def rank_countries(
    resources: Iterable[CountryResourceInput],
    gold: GoldReferenceInput,
) -> list[CountryAssessment]:
    """Országok rangsora a korrigált, aranyhoz viszonyított index alapján."""

    assessments = [assess_country(resource, gold) for resource in resources]
    return sorted(assessments, key=lambda item: item.gold_relative_index, reverse=True)


def civil_axis_gate(index: float) -> tuple[str, float]:
    """A modell eredményét kereskedési kapuvá alakítja.

    Visszatérés: (kapu, pozíciószorzó)
    - ALLOW: megfelelő fundamentális támasz
    - REDUCE: gyenge vagy bizonytalan támasz
    - BLOCK: nagyon gyenge támasz
    """

    if not isfinite(index) or index < 0:
        raise ValueError("Az index csak véges, nem negatív szám lehet")
    if index >= 0.50:
        return "ALLOW", 1.0
    if index >= 0.20:
        return "REDUCE", 0.5
    return "BLOCK", 0.0
