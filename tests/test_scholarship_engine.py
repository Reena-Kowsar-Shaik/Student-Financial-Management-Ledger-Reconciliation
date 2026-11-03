"""
Tests for Scholarship Eligibility and Award Engine.
"""

import unittest
from yottaflex.models.enums import ResidencyStatus, ScholarshipType, ScholarshipStatus, InvoiceLineType, InvoiceStatus
from yottaflex.models.entities import Student, Scholarship, Invoice, InvoiceLine
from yottaflex.engine.scholarship_engine import ScholarshipEngine


class TestScholarshipEngine(unittest.TestCase):

    def setUp(self):
        self.merit_scholarship = Scholarship(
            scholarship_id="SCH-2026-000001",
            code="PRES-EXCELLENCE",
            name="Presidential Academic Excellence Scholarship",
            award_type=ScholarshipType.MERIT,
            funding_source="Endowment",
            max_award_amount=5000.00,
            min_gpa=3.80,
            max_financial_need=100.0,
            eligible_residency="ALL",
            covers_tuition_only=True,
            is_active=True,
        )

        self.need_scholarship = Scholarship(
            scholarship_id="SCH-2026-000002",
            code="NEED-OPPORTUNITY",
            name="Opportunity Need Grant",
            award_type=ScholarshipType.NEED_BASED,
            funding_source="State Grant",
            max_award_amount=4000.00,
            min_gpa=2.50,
            max_financial_need=50.0,
            eligible_residency="IN_STATE",
            covers_tuition_only=True,
            is_active=True,
        )

        self.sample_lines = [
            InvoiceLine("INVL-01", "INV-01", InvoiceLineType.TUITION, "Tuition", 6000.0, 1.0, 6000.0, True),
            InvoiceLine("INVL-02", "INV-01", InvoiceLineType.MANDATORY_FEE, "Fee", 400.0, 1.0, 400.0, False),
        ]

    def test_merit_scholarship_approved(self):
        student = Student("STU-1", "Alice", "W", "a@u.edu", ResidencyStatus.IN_STATE, "PRG-01", gpa=3.90, financial_need_score=20.0)
        award = ScholarshipEngine.evaluate_eligibility("AWD-1", student, self.merit_scholarship, "TERM-2026-FALL", self.sample_lines, "2026-08-15")
        self.assertEqual(award.status, ScholarshipStatus.AWARDED)
        self.assertEqual(award.award_amount, 5000.00)

    def test_merit_scholarship_rejected_low_gpa(self):
        student = Student("STU-2", "Bob", "L", "b@u.edu", ResidencyStatus.IN_STATE, "PRG-01", gpa=3.50, financial_need_score=20.0)
        award = ScholarshipEngine.evaluate_eligibility("AWD-2", student, self.merit_scholarship, "TERM-2026-FALL", self.sample_lines, "2026-08-15")
        self.assertEqual(award.status, ScholarshipStatus.REJECTED)
        self.assertEqual(award.award_amount, 0.0)
        self.assertIn("GPA 3.50 is below minimum requirement of 3.80", award.decision_rationale)

    def test_award_capped_at_eligible_tuition(self):
        # If tuition is only $3,000, award should not exceed $3,000 even if max award is $5,000
        low_lines = [InvoiceLine("INVL-01", "INV-01", InvoiceLineType.TUITION, "Tuition", 3000.0, 1.0, 3000.0, True)]
        student = Student("STU-3", "Charlie", "M", "c@u.edu", ResidencyStatus.IN_STATE, "PRG-01", gpa=3.95, financial_need_score=50.0)
        award = ScholarshipEngine.evaluate_eligibility("AWD-3", student, self.merit_scholarship, "TERM-2026-FALL", low_lines, "2026-08-15")
        self.assertEqual(award.status, ScholarshipStatus.AWARDED)
        self.assertEqual(award.award_amount, 3000.00)

    def test_apply_award_to_invoice(self):
        student = Student("STU-4", "Diana", "K", "d@u.edu", ResidencyStatus.IN_STATE, "PRG-01", gpa=3.90, financial_need_score=20.0)
        award = ScholarshipEngine.evaluate_eligibility("AWD-4", student, self.merit_scholarship, "TERM-2026-FALL", self.sample_lines, "2026-08-15")

        invoice = Invoice("INV-01", "STU-4", "ENR-01", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=6400.0, balance_due=6400.0)
        ScholarshipEngine.apply_award_to_invoice(award, invoice)

        self.assertEqual(invoice.scholarship_credit_amount, 5000.00)
        self.assertEqual(invoice.balance_due, 1400.00)
        self.assertEqual(invoice.status, InvoiceStatus.PARTIALLY_PAID)


if __name__ == "__main__":
    unittest.main()

