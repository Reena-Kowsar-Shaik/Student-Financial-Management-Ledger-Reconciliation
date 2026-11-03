"""
Tests for Anomaly Auditor & Ground Truth Benchmark (Step 5, Step 7, Step 8).
"""

import unittest
from yottaflex.generator.synthetic import SyntheticDataGenerator
from yottaflex.engine.anomaly_auditor import AnomalyAuditor


class TestAnomalyAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        gen = SyntheticDataGenerator(seed=20261022)
        cls.data = gen.generate_all(target_students=500, inject_anomalies=True, anomaly_count=5)
        cls.detected = AnomalyAuditor.audit_all(
            students=cls.data["students"],
            invoices=cls.data["invoices"],
            invoice_lines=cls.data["invoice_lines"],
            awards=cls.data["eligibility_awards"],
            payments=cls.data["payments"],
            allocations=cls.data["allocations"],
            refunds=cls.data["refunds"],
        )
        cls.eval_metrics = AnomalyAuditor.evaluate_against_ground_truth(cls.detected, cls.data["ground_truth"])

    def test_overall_f1_score(self):
        m = self.eval_metrics["overall"]
        self.assertEqual(m["precision"], 1.0)
        self.assertEqual(m["recall"], 1.0)
        self.assertEqual(m["f1_score"], 1.0)
        self.assertEqual(m["false_positives"], 0)
        self.assertEqual(m["false_negatives"], 0)

    def test_all_five_categories_detected(self):
        cats = self.eval_metrics["by_category"]
        expected_cats = [
            "PAYMENT_OVERALLOCATION",
            "SCHOLARSHIP_EXCEEDS_FEES",
            "DUPLICATE_INVOICE",
            "REFUND_EXCEEDS_NET_PAID",
            "BALANCE_LEDGER_DISCREPANCY",
        ]
        for cat in expected_cats:
            self.assertIn(cat, cats)
            self.assertEqual(cats[cat]["precision"], 1.0, f"Precision failed for {cat}")
            self.assertEqual(cats[cat]["recall"], 1.0, f"Recall failed for {cat}")
            self.assertEqual(cats[cat]["f1_score"], 1.0, f"F1 failed for {cat}")


if __name__ == "__main__":
    unittest.main()

