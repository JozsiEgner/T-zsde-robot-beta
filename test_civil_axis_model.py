import unittest

from civil_axis_model import (
    CountryResourceInput,
    GoldReferenceInput,
    assess_country,
    civil_axis_gate,
    rank_countries,
)


class CivilAxisModelTests(unittest.TestCase):
    def setUp(self):
        self.gold = GoldReferenceInput(
            above_ground_quantity=216_000_000_000.0,
            spot_price=75.0,
            world_population=8_100_000_000.0,
        )

    def test_country_assessment_is_non_negative(self):
        china = CountryResourceInput(
            country="Kína",
            reference_product="tőkehal",
            annual_quantity=1_000_000_000.0,
            wholesale_price=4.0,
            country_population=1_410_000_000.0,
            strategic_reserve_value=2_000_000_000_000.0,
            market_cap=10_000_000_000_000.0,
            exchange_turnover=8_000_000_000_000.0,
            open_interest=1_000_000_000_000.0,
            production_capacity_score=1.0,
            co_risk=0.10,
        )
        result = assess_country(china, self.gold)
        self.assertGreaterEqual(result.corrected_country_value, 0.0)
        self.assertGreaterEqual(result.gold_relative_index, 0.0)
        self.assertAlmostEqual(result.environmental_multiplier, 0.90)

    def test_higher_co_risk_reduces_value(self):
        base = dict(
            country="Hollandia",
            reference_product="szarvasmarha",
            annual_quantity=2_000_000.0,
            wholesale_price=2_500.0,
            country_population=18_000_000.0,
            strategic_reserve_value=100_000_000_000.0,
        )
        clean = assess_country(CountryResourceInput(**base, co_risk=0.0), self.gold)
        polluted = assess_country(CountryResourceInput(**base, co_risk=0.5), self.gold)
        self.assertLess(polluted.corrected_country_value, clean.corrected_country_value)

    def test_ranking(self):
        resources = [
            CountryResourceInput("A", "termék-A", 100.0, 10.0, 1_000.0),
            CountryResourceInput("B", "termék-B", 200.0, 10.0, 1_000.0),
        ]
        ranking = rank_countries(resources, self.gold)
        self.assertEqual(ranking[0].country, "B")

    def test_gate(self):
        self.assertEqual(civil_axis_gate(0.60), ("ALLOW", 1.0))
        self.assertEqual(civil_axis_gate(0.30), ("REDUCE", 0.5))
        self.assertEqual(civil_axis_gate(0.10), ("BLOCK", 0.0))


if __name__ == "__main__":
    unittest.main()
