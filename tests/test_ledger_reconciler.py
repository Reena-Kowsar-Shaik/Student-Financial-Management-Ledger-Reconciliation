"""
Tests for General Ledger and Account Reconciliation Engine.
"""

import unittest
from yottaflex.models.enums import InvoiceStatus, PaymentMethod, PaymentStatus, RefundReason, RefundStatus, ScholarshipStatus, LedgerEntryType
from yottaflex.models.entities import Invoice, Eligibility, Payment, Refund
from yottaflex.engine.ledger_reconciler import LedgerReconciler


class TestLedgerReconciler(unittest.TestCase):

    def test_reconciliation_balanced_account(self):
        student_id = "STU-01"
        invoices = [Invoice("INV-01", student_id, "ENR-01", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=5000.0, scholarship_credit_amount=2000.0, payment_credit_amount=3000.0, balance_due=0.0, status=InvoiceStatus.PAID)]
        awards = [Eligibility("AWD-01", "SCH-01", student_id, "TERM-2026-FALL", award_amount=2000.0, eligible_amount=5000.0, status=ScholarshipStatus.APPLIED, evaluation_date="2026-08-15")]
        payments = [Payment("PAY-01", student_id, "TERM-2026-FALL", "2026-08-20", PaymentMethod.ACH_TRANSFER, total_amount=3000.0, allocated_amount=3000.0, unallocated_amount=0.0, status=PaymentStatus.SETTLED)]
        refunds = []

        recon = LedgerReconciler.reconcile_student(student_id, invoices, awards, payments, refunds)

        self.assertTrue(recon["is_reconciled"])
        self.assertEqual(recon["discrepancy"], 0.0)
        self.assertEqual(recon["ledger_net_balance"], 0.0)
        self.assertEqual(recon["account_current_balance"], 0.0)

    def test_reconciliation_detects_corrupted_discrepancy(self):
        student_id = "STU-02"
        # Phantom discount on invoice balance: balance_due reported as $500 instead of $1,000
        invoices = [Invoice("INV-02", student_id, "ENR-02", "TERM-2026-FALL", "2026-08-15", "2026-09-15", subtotal_amount=5000.0, scholarship_credit_amount=2000.0, payment_credit_amount=2000.0, balance_due=500.0)]
        awards = [Eligibility("AWD-02", "SCH-01", student_id, "TERM-2026-FALL", award_amount=2000.0, eligible_amount=5000.0, status=ScholarshipStatus.APPLIED, evaluation_date="2026-08-15")]
        payments = [Payment("PAY-02", student_id, "TERM-2026-FALL", "2026-08-20", PaymentMethod.ACH_TRANSFER, total_amount=2000.0, allocated_amount=2000.0, unallocated_amount=0.0, status=PaymentStatus.SETTLED)]
        refunds = []

        recon = LedgerReconciler.reconcile_student(student_id, invoices, awards, payments, refunds)

        self.assertFalse(recon["is_reconciled"])
        # Ledger net balance: 5000 - 2000 - 2000 = 1000. Reported invoice balance: 500. Discrepancy: 500.
        self.assertEqual(recon["ledger_net_balance"], 1000.0)
        self.assertEqual(recon["account_current_balance"], 500.0)
        self.assertEqual(recon["discrepancy"], 500.0)


if __name__ == "__main__":
    unittest.main()

