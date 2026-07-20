import unittest
from unittest.mock import patch

from dollar_proxy_thermometer import SeriesPoint, calculate_reading


def make_series(series_id: str, start: float, step: float, count: int = 30):
    return [
        SeriesPoint(
            series_id=series_id,
            date=f"2026-07-{(i % 20) + 1:02d}",
            value=start + step * i,
            source_url="https://fred.stlouisfed.org/",
        )
        for i in range(count)
    ]


class DollarProxyThermometerTests(unittest.TestCase):
    @patch("dollar_proxy_thermometer._age_days", return_value=0)
    def test_rising_dollar_and_real_yield_raise_score(self, _mock_age):
        reading = calculate_reading(
            make_series("DTWEXBGS", 100.0, 0.25),
            make_series("DFII10", 1.0, 0.05),
            make_series("VIXCLS", 25.0, 0.0),
        )
        self.assertGreater(reading.score, 50.0)
        self.assertIn(reading.gate, {"REDUCE", "BLOCK"})

    @patch("dollar_proxy_thermometer._age_days", return_value=0)
    def test_falling_conditions_allow(self, _mock_age):
        reading = calculate_reading(
            make_series("DTWEXBGS", 120.0, -0.20),
            make_series("DFII10", 3.0, -0.04),
            make_series("VIXCLS", 14.0, 0.0),
        )
        self.assertEqual(reading.gate, "ALLOW")
        self.assertEqual(reading.position_multiplier, 1.0)

    @patch("dollar_proxy_thermometer._age_days", return_value=30)
    def test_stale_data_blocks(self, _mock_age):
        reading = calculate_reading(
            make_series("DTWEXBGS", 100.0, 0.0),
            make_series("DFII10", 2.0, 0.0),
            make_series("VIXCLS", 20.0, 0.0),
            stale_after_days=10,
        )
        self.assertTrue(reading.stale)
        self.assertEqual(reading.gate, "BLOCK")


if __name__ == "__main__":
    unittest.main()
