"""
Tests for Data Integrity and Acceptance Validator (Step 8).
"""

import unittest
from yottaflex.generator.synthetic import SyntheticDataGenerator
from yottaflex.validator.data_integrity import DataIntegrityValidator


class TestDataIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        gen = SyntheticDataGenerator(seed=20261022)
        cls.data = gen.generate_all(target_students=300, inject_anomalies=False)

    def test_acceptance_data_integrity(self):
        report = DataIntegrityValidator.validate_dataset(self.data)
        self.assertTrue(report["is_valid"], f"Integrity validation failed: {report['details']}")
        self.assertEqual(report["checks_failed"], 0)
        self.assertGreaterEqual(report["checks_passed"], 5)


if __name__ == "__main__":
    unittest.main()

