"""
Payment Processing and Allocation Engine.
Allocates payments to invoices and invoice lines with FIFO/priority ordering,
handling partial payments, full settlements, and unallocated overpayments.
"""

from typing import List, Tuple, Optional
from datetime import datetime
from yottaflex.models.enums import (
    InvoiceStatus,
    PaymentStatus,
    AllocationStatus,
)
from yottaflex.models.entities import (
    Payment,
    PaymentAllocation,
    Invoice,
    InvoiceLine,
)


class PaymentAllocator:
    """
    Manages payment application and ledger allocation.
    """

    @classmethod
    def allocate_payment(
        cls,
        payment: Payment,
        invoices: List[Invoice],
        invoice_lines_by_inv_id: Optional[dict] = None,
        allocation_date: Optional[str] = None,
    ) -> List[PaymentAllocation]:
        """
        Allocates a payment across eligible open invoices (FIFO order by issue_date).
        Returns the list of PaymentAllocation records created.
        """
        allocations: List[PaymentAllocation] = []
        date_str = allocation_date or payment.payment_date
        remaining_funds = payment.total_amount - payment.allocated_amount

        if remaining_funds <= 0:
            return allocations

        # Filter and sort unpaid/partially paid invoices by issue date
        eligible_invoices = [
            inv for inv in invoices
            if inv.balance_due > 0 and inv.status not in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED)
        ]
        eligible_invoices.sort(key=lambda x: x.issue_date)

        alloc_counter = 1
        for invoice in eligible_invoices:
            if remaining_funds <= 0:
                break

            amount_to_apply = round(min(remaining_funds, invoice.balance_due), 2)
            if amount_to_apply <= 0:
                continue

            # Optional: link to specific invoice line if line items provided
            target_line_id = None
            if invoice_lines_by_inv_id and invoice.invoice_id in invoice_lines_by_inv_id:
                lines = invoice_lines_by_inv_id[invoice.invoice_id]
                if lines:
                    target_line_id = lines[0].invoice_line_id

            allocation_id = f"ALLOC-{payment.payment_id}-{alloc_counter:02d}"
            allocation = PaymentAllocation(
                allocation_id=allocation_id,
                payment_id=payment.payment_id,
                invoice_id=invoice.invoice_id,
                invoice_line_id=target_line_id,
                allocated_amount=amount_to_apply,
                allocation_date=date_str,
                status=AllocationStatus.ALLOCATED,
            )
            allocations.append(allocation)
            alloc_counter += 1

            # Update invoice state
            invoice.payment_credit_amount = round(invoice.payment_credit_amount + amount_to_apply, 2)
            invoice.balance_due = round(max(0.0, invoice.subtotal_amount - invoice.scholarship_credit_amount - invoice.payment_credit_amount), 2)

            if invoice.balance_due == 0:
                invoice.status = InvoiceStatus.PAID
            else:
                invoice.status = InvoiceStatus.PARTIALLY_PAID

            # Update payment tracking
            remaining_funds = round(remaining_funds - amount_to_apply, 2)
            payment.allocated_amount = round(payment.allocated_amount + amount_to_apply, 2)

        # Unallocated excess is stored as credit balance
        payment.unallocated_amount = round(max(0.0, remaining_funds), 2)
        payment.status = PaymentStatus.SETTLED

        return allocations

