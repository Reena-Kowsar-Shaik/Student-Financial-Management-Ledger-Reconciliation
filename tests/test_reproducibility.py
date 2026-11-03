"""
Tests for Deterministic Seed Reproducibility (Step 10).
Regenerates twice with seed 20261022 and verifies identical SHA-256 checksums across all exports.
"""

import os
import shutil
import unittest
from yottaflex.generator.synthetic import SyntheticDataGenerator


class TestReproducibility(unittest.TestCase):

    def test_reproducible_sha256_checksums(self):
        dir1 = "data/test_repro_1"
        dir2 = "data/test_repro_2"

        try:
            gen1 = SyntheticDataGenerator(seed=20261022)
            d1 = gen1.generate_all(target_students=200, inject_anomalies=True)
            m1 = gen1.export_data(d1, output_dir=dir1)

            gen2 = SyntheticDataGenerator(seed=20261022)
            d2 = gen2.generate_all(target_students=200, inject_anomalies=True)
            m2 = gen2.export_data(d2, output_dir=dir2)

            self.assertEqual(len(m1), len(m2))
            for filename, sha1 in m1.items():
                self.assertIn(filename, m2)
                sha2 = m2[filename]
                self.assertEqual(sha1, sha2, f"Checksum mismatch for file {filename}: {sha1} != {sha2}")
        finally:
            shutil.rmtree(dir1, ignore_errors=True)
            shutil.rmtree(dir2, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
