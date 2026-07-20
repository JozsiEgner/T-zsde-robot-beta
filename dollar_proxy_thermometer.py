from __future__ import annotations

import csv
import io
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


@dataclass(frozen=True)
class SeriesPoint:
    series_id: str
    date: str
    value: float
    source_url: str


@dataclass(frozen=True)
class DollarProxyReading:
    score: float
    state: str
    gate: str
    position_multiplier: float
    broad_dollar: SeriesPoint
    real_yield_10y: SeriesPoint
    vix: SeriesPoint
    broad_dollar_change_20: float
    real_yield_change_20: float
    vix_level: float
    fetched_at_utc: str
    stale: bool


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _download_csv(series_id: str, timeout: float = 10.0) -> str:
    url = FRED_CSV_URL.format(series_id=series_id)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Ezo-Trading-Robot/1.0 (paper-trading research)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _parse_valid_rows(series_id: str, csv_text: str) -> list[SeriesPoint]:
    rows: list[SeriesPoint] = []
    reader = csv.DictReader(io.StringIO(csv_text))
    value_column = series_id
    for row in reader:
        raw = (row.get(value_column) or "").strip()
        if raw in {"", "."}:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        rows.append(
            SeriesPoint(
                series_id=series_id,
                date=(row.get("DATE") or row.get("observation_date") or "").strip(),
                value=value,
                source_url=FRED_CSV_URL.format(series_id=series_id),
            )
        )
    if not rows:
        raise RuntimeError(f"Nincs használható FRED adat: {series_id}")
    return rows


def _series(series_id: str, timeout: float = 10.0) -> list[SeriesPoint]:
    return _parse_valid_rows(series_id, _download_csv(series_id, timeout))


def _pct_change(points: list[SeriesPoint], periods: int) -> float:
    if len(points) <= periods:
        raise RuntimeError(f"Kevés adat a {periods} periódusos változáshoz")
    latest = points[-1].value
    previous = points[-1 - periods].value
    if previous == 0:
        return 0.0
    return latest / previous - 1.0


def _absolute_change(points: list[SeriesPoint], periods: int) -> float:
    if len(points) <= periods:
        raise RuntimeError(f"Kevés adat a {periods} periódusos változáshoz")
    return points[-1].value - points[-1 - periods].value


def _age_days(date_text: str) -> int:
    point_date = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - point_date).days)


def calculate_reading(
    broad_dollar_rows: list[SeriesPoint],
    real_yield_rows: list[SeriesPoint],
    vix_rows: list[SeriesPoint],
    *,
    stale_after_days: int = 10,
) -> DollarProxyReading:
    """0..100 dollár-/finanszírozási nyomás hőmérő.

    Súlyok:
    - 50% Fed széles, kereskedelmi súlyozású dollárindex 20 megfigyeléses változása
    - 30% 10 éves amerikai reálhozam 20 megfigyeléses változása
    - 20% VIX aktuális stresszszintje

    Ez saját kompozit indikátor, nem hivatalos Fed- vagy FRED-mutató.
    """

    dollar_change = _pct_change(broad_dollar_rows, 20)
    real_yield_change = _absolute_change(real_yield_rows, 20)
    vix_level = vix_rows[-1].value

    # Normalizálás 0..100 tartományra. A középérték 50.
    dollar_component = clamp(50.0 + dollar_change * 1000.0, 0.0, 100.0)
    real_yield_component = clamp(50.0 + real_yield_change * 25.0, 0.0, 100.0)
    vix_component = clamp((vix_level - 10.0) / 30.0 * 100.0, 0.0, 100.0)

    score = 0.50 * dollar_component + 0.30 * real_yield_component + 0.20 * vix_component

    if score >= 75.0:
        state, gate, multiplier = "FORRÓ", "BLOCK", 0.0
    elif score >= 60.0:
        state, gate, multiplier = "MELEG", "REDUCE", 0.5
    elif score >= 40.0:
        state, gate, multiplier = "SEMLEGES", "ALLOW", 1.0
    elif score >= 25.0:
        state, gate, multiplier = "HŰVÖS", "ALLOW", 1.0
    else:
        state, gate, multiplier = "HIDEG", "ALLOW", 1.0

    latest_points = (broad_dollar_rows[-1], real_yield_rows[-1], vix_rows[-1])
    stale = any(_age_days(point.date) > stale_after_days for point in latest_points)
    if stale:
        gate, multiplier = "BLOCK", 0.0

    return DollarProxyReading(
        score=score,
        state=state,
        gate=gate,
        position_multiplier=multiplier,
        broad_dollar=broad_dollar_rows[-1],
        real_yield_10y=real_yield_rows[-1],
        vix=vix_rows[-1],
        broad_dollar_change_20=dollar_change,
        real_yield_change_20=real_yield_change,
        vix_level=vix_level,
        fetched_at_utc=datetime.now(timezone.utc).isoformat(),
        stale=stale,
    )


def fetch_dollar_proxy_reading(
    *,
    timeout: float = 10.0,
    stale_after_days: int = 10,
) -> DollarProxyReading:
    return calculate_reading(
        _series("DTWEXBGS", timeout),
        _series("DFII10", timeout),
        _series("VIXCLS", timeout),
        stale_after_days=stale_after_days,
    )


class DollarProxyCache:
    def __init__(self, cache_path: str = ".cache/dollar_proxy.json", ttl_seconds: int = 3600):
        self.cache_path = Path(cache_path)
        self.ttl_seconds = max(60, ttl_seconds)
        self._reading: DollarProxyReading | None = None
        self._loaded_at = 0.0

    def get(self, *, timeout: float = 10.0, stale_after_days: int = 10) -> DollarProxyReading:
        now = time.time()
        if self._reading is not None and now - self._loaded_at < self.ttl_seconds:
            return self._reading

        reading = fetch_dollar_proxy_reading(timeout=timeout, stale_after_days=stale_after_days)
        self._reading = reading
        self._loaded_at = now
        self._save_audit(reading)
        return reading

    def _save_audit(self, reading: DollarProxyReading) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "score": reading.score,
            "state": reading.state,
            "gate": reading.gate,
            "position_multiplier": reading.position_multiplier,
            "stale": reading.stale,
            "fetched_at_utc": reading.fetched_at_utc,
            "broad_dollar": reading.broad_dollar.__dict__,
            "real_yield_10y": reading.real_yield_10y.__dict__,
            "vix": reading.vix.__dict__,
            "broad_dollar_change_20": reading.broad_dollar_change_20,
            "real_yield_change_20": reading.real_yield_change_20,
            "vix_level": reading.vix_level,
        }
        self.cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
