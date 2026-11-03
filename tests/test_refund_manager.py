"""
Tests for Refund Manager and Cancellation Processing.
"""

import unittest
from yottaflex.models.enums import PaymentMethod, PaymentStatus, RefundReason, RefundStatus
from yottaflex.models.entities import Payment, Refund
from yottaflex.engine.refund_manager import RefundManager


class TestRefundManager(unittest.TestCase):

    def test_valid_refund_within_net_paid(self):
        payment = Payment("PAY-01", "STU-01", "TERM-2026-FALL", "2026-08-20", PaymentMethod.ACH_TRANSFER, total_amount=3000.0, status=PaymentStatus.SETTLED)

        refund, success = RefundManager.process_refund(
            refund_id="REF-01",
            student_id="STU-01",
            payment=payment,
            term_id="TERM-2026-FALL",
            requested_amount=1000.0,
            reason=RefundReason.OVERPAYMENT,
            request_date="2026-09-01",
            all_student_payments=[payment],
            existing_refunds=[],
        )

        self.assertTrue(success)
        self.assertEqual(refund.status, RefundStatus.PROCESSED)
        self.assertEqual(refund.refund_amount, 1000.0)
        self.assertEqual(payment.status, PaymentStatus.PARTIALLY_REFUNDED)

    def test_refund_rejected_exceeds_net_paid(self):
        payment = Payment("PAY-02", "STU-02", "TERM-2026-FALL", "2026-08-20", PaymentMethod.CREDIT_CARD, total_amount=2000.0, status=PaymentStatus.SETTLED)

        # Requesting $2,500 when net paid is only $2,000
        refund, success = RefundManager.process_refund(
            refund_id="REF-02",
            student_id="STU-02",
            payment=payment,
            term_id="TERM-2026-FALL",
            requested_amount=2500.0,
            reason=RefundReason.WITHDRAWAL,
            request_date="2026-09-01",
            all_student_payments=[payment],
            existing_refunds=[],
        )

        self.assertFalse(success)
        self.assertEqual(refund.status, RefundStatus.REJECTED)
        self.assertIn("exceeds net settled payments", refund.approval_notes)


if __name__ == "__main__":
    unittest.main()
