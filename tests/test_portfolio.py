import unittest
from risk_app.portfolio import default_portfolio, stress_portfolio, class_contributions

class TestPortfolio(unittest.TestCase):
    def test_has_required_asset_classes_and_positions(self):
        df = default_portfolio()
        self.assertGreaterEqual(len(df), 10)
        self.assertTrue({"Equity","Bond","Loan","Derivative"}.issubset(set(df.asset_class)))
    def test_stress_reproducible_and_values_conserve(self):
        p = default_portfolio()
        a, sa = stress_portfolio(p, "Credit crisis", 1.0)
        b, sb = stress_portfolio(p, "Credit crisis", 1.0)
        self.assertAlmostEqual(sa["after_value"], sb["after_value"])
        self.assertAlmostEqual(a.after_value.sum(), sa["after_value"])
        self.assertLess(sa["after_value"], sa["before_value"])
        self.assertGreater(sa["absolute_loss"], 0)
    def test_zero_severity_no_change(self):
        _, s = stress_portfolio(default_portfolio(), "Credit crisis", 0)
        self.assertAlmostEqual(s["before_value"], s["after_value"])
        self.assertEqual(s["loss_pct"], 0)
    def test_invalid_severity_rejected(self):
        with self.assertRaises(ValueError): stress_portfolio(default_portfolio(), "Credit crisis", 4)
    def test_class_contributions(self):
        details, _ = stress_portfolio(default_portfolio(), "Credit crisis")
        self.assertGreaterEqual(len(class_contributions(details)), 4)
if __name__ == "__main__": unittest.main()
