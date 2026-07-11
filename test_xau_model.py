import unittest

from xau_model import (
    MarketState,
    XauFundamentals,
    assess_xau,
    cost_of_carry_fair_value,
    divergence_angle,
)


class XauModelTests(unittest.TestCase):
    def test_cost_of_carry_is_positive(self):
        fair = cost_of_carry_fair_value(2000.0, 0.04, 0.003, 0.0, 1 / 12)
        self.assertGreater(fair, 2000.0)

    def test_parallel_vectors_have_small_angle(self):
        self.assertAlmostEqual(divergence_angle([1, 1], [2, 2]), 0.0, places=6)

    def test_large_residual_blocks(self):
        result = assess_xau(
            fundamentals=XauFundamentals(dxy_change=-0.5, real_yield_change=-0.5),
            market=MarketState(0.5, 0.4, 0.2, 0.8),
            spot=2100.0,
            forward=2005.0,
            years=1 / 12,
            rate=0.04,
            storage=0.003,
            convenience_yield=0.0,
            residual_mean=0.0,
            residual_std=10.0,
            basis_mean=0.0,
            basis_std=10.0,
        )
        self.assertEqual(result.gate, "BLOCK")
        self.assertEqual(result.position_multiplier, 0.0)


if __name__ == "__main__":
    unittest.main()
