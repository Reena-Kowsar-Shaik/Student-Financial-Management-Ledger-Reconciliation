"""
Refund and Cancellation Processing Engine.
Enforces net-paid boundary constraints, term withdrawal schedules, and audit trails.
"""

from typing import List, Optional, Tuple
from datetime import datetime, date
from yottaflex.models.enums import (
    RefundReason,
    RefundStatus,
    PaymentStatus,
    EnrollmentStatus,
    InvoiceStatus,
)
from yottaflex.models.entities import (
    Refund,
    Payment,
    Enrollment,
    Invoice,
)


class RefundManager:
    """
    Manages refund validations, withdrawal pro-rations, and payment settlement adjustments.
    """

    @staticmethod
    def calculate_net_paid(
        student_id: str,
        payments: List[Payment],
        existing_refunds: List[Refund],
    ) -> float:
        """
        Calculates net settled cash received: sum(settled payments) - sum(processed refunds).
        """
        settled_sum = sum(
            p.total_amount for p in payments
            if p.student_id == student_id and p.status in (
                PaymentStatus.SETTLED, PaymentStatus.PARTIALLY_REFUNDED
            )
        )
        refunded_sum = sum(
            r.refund_amount for r in existing_refunds
            if r.student_id == student_id and r.status == RefundStatus.PROCESSED
        )
        return round(max(0.0, settled_sum - refunded_sum), 2)

    @classmethod
    def process_refund(
        cls,
        refund_id: str,
        student_id: str,
        payment: Payment,
        term_id: str,
        requested_amount: float,
        reason: RefundReason,
        request_date: str,
        all_student_payments: List[Payment],
        existing_refunds: List[Refund],
        approval_notes: str = "",
    ) -> Tuple[Refund, bool]:
        """
        Processes a refund if within net-paid boundary constraints.
        Returns the Refund entity and a boolean indicating whether it was approved/processed.
        """
        net_paid = cls.calculate_net_paid(student_id, all_student_payments, existing_refunds)

        if requested_amount <= 0:
            refund = Refund(
                refund_id=refund_id,
                student_id=student_id,
                payment_id=payment.payment_id,
                term_id=term_id,
                request_date=request_date,
                processed_date=None,
                refund_amount=requested_amount,
                reason=reason,
                status=RefundStatus.REJECTED,
                approval_notes="Refund request amount must be greater than zero.",
            )
            return refund, False

        if requested_amount > round(net_paid + 0.01, 2):
            refund = Refund(
                refund_id=refund_id,
                student_id=student_id,
                payment_id=payment.payment_id,
                term_id=term_id,
                request_date=request_date,
                processed_date=None,
                refund_amount=requested_amount,
                reason=reason,
                status=RefundStatus.REJECTED,
                approval_notes=f"Requested ${requested_amount:.2f} exceeds net settled payments of ${net_paid:.2f}.",
            )
            return refund, False

        # Process valid refund
        refund = Refund(
            refund_id=refund_id,
            student_id=student_id,
            payment_id=payment.payment_id,
            term_id=term_id,
            request_date=request_date,
            processed_date=request_date,
            refund_amount=round(requested_amount, 2),
            reason=reason,
            status=RefundStatus.PROCESSED,
            approval_notes=approval_notes or f"Approved ${requested_amount:.2f} refund against {payment.payment_id}.",
        )

        # Deduct from unallocated credit if refunding an overpayment
        if payment.unallocated_amount >= requested_amount:
            payment.unallocated_amount = round(payment.unallocated_amount - requested_amount, 2)
        else:
            payment.unallocated_amount = 0.0

        # Update payment status
        if requested_amount >= payment.total_amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        return refund, True
