import unittest
from risk_app.nlp import analyze_text, classify_event, impact_score

class TestNLP(unittest.TestCase):
    def test_signed_sentiment_bounded(self):
        result = analyze_text("Company reports strong profit growth and beats earnings expectations")
        self.assertGreaterEqual(result["sentiment"], -1)
        self.assertLessEqual(result["sentiment"], 1)
        self.assertGreater(result["sentiment"], 0)
    def test_event_classification(self):
        self.assertEqual(classify_event("Bankruptcy after missed payment and credit default"), "Credit Event")
        self.assertEqual(classify_event("Central bank raises interest rate due to inflation"), "Macroeconomic")
    def test_impact_range(self):
        self.assertTrue(1 <= impact_score("War and bankruptcy trigger emergency") <= 10)
    def test_output_contract(self):
        out = analyze_text("Regional lender faces credit downgrade")
        self.assertEqual(set(["sentiment","event_type","impact","model"]).issubset(out), True)
        self.assertIsInstance(out["impact"], int)
if __name__ == "__main__": unittest.main()
