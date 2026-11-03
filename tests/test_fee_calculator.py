"""
Tests for Tuition and Fee Calculation Engine.
"""

import unittest
from datetime import date
from yottaflex.models.enums import ResidencyStatus, DegreeLevel, InvoiceLineType, InvoiceStatus
from yottaflex.models.entities import Student, Program, FeeSchedule, Enrollment
from yottaflex.engine.fee_calculator import FeeCalculator


class TestFeeCalculator(unittest.TestCase):

    def setUp(self):
        self.program = Program(
            program_id="PRG-001",
            name="B.S. in Computer Science",
            degree_level=DegreeLevel.UNDERGRADUATE,
            department="School of Computing",
            credits_required=120,
            base_tuition_per_credit=500.00,
            mandatory_fee=300.00,
            lab_fee_per_credit=50.00,
            is_active=True,
        )

        self.fee_schedule = FeeSchedule(
            fee_schedule_id="FS-2026-FALL-PRG-001",
            program_id="PRG-001",
            term_id="TERM-2026-FALL",
            effective_start_date="2026-08-25",
            effective_end_date="2026-12-18",
            tuition_per_credit=500.00,
            mandatory_fee=300.00,
            technology_fee=100.00,
            lab_fee_per_credit=50.00,
            out_of_state_multiplier=1.65,
            international_multiplier=2.10,
            late_fee_amount=75.00,
            late_fee_grace_days=14,
        )

    def test_tuition_rate_by_residency(self):
        # In-state
        in_state_rate = FeeCalculator.calculate_tuition_rate(self.fee_schedule, ResidencyStatus.IN_STATE)
        self.assertEqual(in_state_rate, 500.00)

        # Out-of-state: 500 * 1.65 = 825.00
        oos_rate = FeeCalculator.calculate_tuition_rate(self.fee_schedule, ResidencyStatus.OUT_OF_STATE)
        self.assertEqual(oos_rate, 825.00)

        # International: 500 * 2.10 = 1050.00
        intl_rate = FeeCalculator.calculate_tuition_rate(self.fee_schedule, ResidencyStatus.INTERNATIONAL)
        self.assertEqual(intl_rate, 1050.00)

    def test_invoice_generation_line_items(self):
        student = Student(
            student_id="STU-000001",
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@university.edu",
            residency_status=ResidencyStatus.IN_STATE,
            program_id="PRG-001",
            gpa=3.85,
            financial_need_score=50.0,
        )

        enrollment = Enrollment(
            enrollment_id="ENR-2026-000001",
            student_id="STU-000001",
            program_id="PRG-001",
            term_id="TERM-2026-FALL",
            credits_enrolled=12,
            enrollment_date="2026-08-15",
            fee_waiver_percent=0.0,
        )

        invoice, lines = FeeCalculator.generate_invoice(
            invoice_id="INV-STU-000001-2026-000001",
            student=student,
            program=self.program,
            fee_schedule=self.fee_schedule,
            enrollment=enrollment,
            issue_date="2026-08-15",
        )

        # Expected:
        # Tuition: 12 * $500 = $6,000
        # Mandatory Fee: $300
        # Technology Fee: $100
        # Lab Fee: 12 * $50 = $600
        # Total: $7,000
        self.assertEqual(invoice.subtotal_amount, 7000.00)
        self.assertEqual(invoice.balance_due, 7000.00)
        self.assertEqual(len(lines), 4)

    def test_fee_waiver_discount(self):
        student = Student(
            student_id="STU-000002",
            first_name="John",
            last_name="Smith",
            email="john.smith@university.edu",
            residency_status=ResidencyStatus.IN_STATE,
            program_id="PRG-001",
            gpa=3.95,
            financial_need_score=20.0,
        )

        # 25% waiver on tuition
        enrollment = Enrollment(
            enrollment_id="ENR-2026-000002",
            student_id="STU-000002",
            program_id="PRG-001",
            term_id="TERM-2026-FALL",
            credits_enrolled=10,
            enrollment_date="2026-08-15",
            fee_waiver_percent=25.0,
        )

        invoice, lines = FeeCalculator.generate_invoice(
            invoice_id="INV-STU-000002-2026-000001",
            student=student,
            program=self.program,
            fee_schedule=self.fee_schedule,
            enrollment=enrollment,
            issue_date="2026-08-15",
        )

        # Tuition: 10 * 500 = 5000
        # Mandatory: 300, Tech: 100, Lab: 10 * 50 = 500
        # Waiver: -25% of 5000 = -1250
        # Subtotal: 5000 + 300 + 100 + 500 - 1250 = 4650.00
        self.assertEqual(invoice.subtotal_amount, 4650.00)
        waiver_line = next(l for l in lines if l.line_type == InvoiceLineType.FEE_WAIVER)
        self.assertEqual(waiver_line.line_total, -1250.00)

    def test_late_fee_assessment(self):
        student = Student(
            student_id="STU-000003",
            first_name="Late",
            last_name="Payer",
            email="late@university.edu",
            residency_status=ResidencyStatus.IN_STATE,
            program_id="PRG-001",
            gpa=3.0,
            financial_need_score=50.0,
        )
        enrollment = Enrollment(
            enrollment_id="ENR-2026-000003",
            student_id="STU-000003",
            program_id="PRG-001",
            term_id="TERM-2026-FALL",
            credits_enrolled=12,
            enrollment_date="2026-08-15",
        )
        invoice, lines = FeeCalculator.generate_invoice(
            invoice_id="INV-STU-000003-2026-000001",
            student=student,
            program=self.program,
            fee_schedule=self.fee_schedule,
            enrollment=enrollment,
            issue_date="2026-08-15",
            due_days=30,  # due: 2026-09-14, grace 14d -> 2026-09-28
        )

        # As of 2026-09-20 (within grace): No late fee
        assessed_early = FeeCalculator.assess_late_fee(invoice, lines, self.fee_schedule, as_of_date="2026-09-20")
        self.assertFalse(assessed_early)

        # As of 2026-10-01 (past grace): Late fee assessed
        assessed_late = FeeCalculator.assess_late_fee(invoice, lines, self.fee_schedule, as_of_date="2026-10-01")
        self.assertTrue(assessed_late)
        self.assertEqual(invoice.status, InvoiceStatus.OVERDUE)
        self.assertEqual(invoice.subtotal_amount, 7075.00)


if __name__ == "__main__":
    unittest.main()

