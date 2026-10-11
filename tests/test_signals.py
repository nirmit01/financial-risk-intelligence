import unittest
from risk_app.signals import generate_risk_signal

class TestSignals(unittest.TestCase):
    def test_credit_signal_maps_to_credit_crisis(self):
        s = generate_risk_signal({"event_type":"Credit Event","impact":9})
        self.assertEqual(s["scenario"], "Credit crisis")
        self.assertEqual(s["priority"], "High")
        self.assertLessEqual(s["suggested_severity"], 2)
    def test_other_high_impact_falls_back_to_liquidity(self):
        s = generate_risk_signal({"event_type":"Other","impact":8})
        self.assertEqual(s["scenario"], "Market liquidity shock")
if __name__ == "__main__": unittest.main()
