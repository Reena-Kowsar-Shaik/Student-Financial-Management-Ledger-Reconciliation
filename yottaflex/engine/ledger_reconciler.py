"""
General Ledger and Student Account Reconciliation Engine.
Calculates double-entry accounting entries, reconciles student accounts, and detects discrepancies.
"""

from typing import List, Dict, Any, Tuple
from yottaflex.models.enums import (
    InvoiceStatus,
    PaymentStatus,
    RefundStatus,
    ScholarshipStatus,
    LedgerEntryType,
)
from yottaflex.models.entities import (
    Student,
    Invoice,
    Eligibility,
    Payment,
    Refund,
    StudentLedgerEntry,
)


class LedgerReconciler:
    """
    Maintains immutable student financial ledger entries and performs account reconciliation.
    """

    @classmethod
    def generate_ledger_entries(
        cls,
        student_id: str,
        invoices: List[Invoice],
        awards: List[Eligibility],
        payments: List[Payment],
        refunds: List[Refund],
    ) -> List[StudentLedgerEntry]:
        """
        Builds an immutable, time-ordered double-entry ledger of transactions for a student.
        """
        raw_events = []

        # 1. Invoice Debits (Student owes tuition & fees)
        for inv in invoices:
            if inv.student_id == student_id and inv.status != InvoiceStatus.CANCELLED:
                raw_events.append({
                    "date": inv.issue_date,
                    "type": LedgerEntryType.DEBIT,
                    "source_type": "INVOICE",
                    "source_id": inv.invoice_id,
                    "amount": inv.subtotal_amount,
                    "term_id": inv.term_id,
                    "description": f"Tuition & Fees Invoiced ({inv.invoice_id})",
                })

        # 2. Scholarship Credits (Institutional aid reduces obligation)
        for awd in awards:
            if awd.student_id == student_id and awd.status in (ScholarshipStatus.AWARDED, ScholarshipStatus.APPLIED):
                raw_events.append({
                    "date": awd.evaluation_date or "2026-08-15",
                    "type": LedgerEntryType.CREDIT,
                    "source_type": "SCHOLARSHIP",
                    "source_id": awd.award_id,
                    "amount": awd.award_amount,
                    "term_id": awd.term_id,
                    "description": f"Scholarship Award Applied ({awd.award_id})",
                })

        # 3. Payment Credits (Cash/ACH/Card receipt reduces obligation)
        for pay in payments:
            if pay.student_id == student_id and pay.status in (PaymentStatus.SETTLED, PaymentStatus.PARTIALLY_REFUNDED):
                raw_events.append({
                    "date": pay.payment_date,
                    "type": LedgerEntryType.CREDIT,
                    "source_type": "PAYMENT",
                    "source_id": pay.payment_id,
                    "amount": pay.total_amount,
                    "term_id": pay.term_id,
                    "description": f"Payment Received ({pay.payment_method.value if hasattr(pay.payment_method, 'value') else pay.payment_method} - {pay.payment_id})",
                })

        # 4. Refund Debits (Disbursing cash back increases net student obligation)
        for ref in refunds:
            if ref.student_id == student_id and ref.status == RefundStatus.PROCESSED:
                raw_events.append({
                    "date": ref.processed_date or ref.request_date,
                    "type": LedgerEntryType.DEBIT,
                    "source_type": "REFUND",
                    "source_id": ref.refund_id,
                    "amount": ref.refund_amount,
                    "term_id": ref.term_id,
                    "description": f"Refund Disbursed ({ref.reason.value if hasattr(ref.reason, 'value') else ref.reason} - {ref.refund_id})",
                })

        # Sort chronologically
        raw_events.sort(key=lambda x: (x["date"], 0 if x["type"] == LedgerEntryType.DEBIT else 1))

        ledger_entries: List[StudentLedgerEntry] = []
        running_bal = 0.0

        for i, ev in enumerate(raw_events, start=1):
            if ev["type"] == LedgerEntryType.DEBIT:
                running_bal += ev["amount"]
            else:
                running_bal -= ev["amount"]
            running_bal = round(running_bal, 2)

            entry = StudentLedgerEntry(
                entry_id=f"LED-{student_id}-{i:03d}",
                student_id=student_id,
                term_id=ev["term_id"],
                transaction_date=ev["date"],
                entry_type=ev["type"],
                source_entity_type=ev["source_type"],
                source_entity_id=ev["source_id"],
                amount=round(ev["amount"], 2),
                running_balance=running_bal,
                description=ev["description"],
            )
            ledger_entries.append(entry)

        return ledger_entries

    @classmethod
    def reconcile_student(
        cls,
        student_id: str,
        invoices: List[Invoice],
        awards: List[Eligibility],
        payments: List[Payment],
        refunds: List[Refund],
    ) -> Dict[str, Any]:
        """
        Reconciles a student's balance across all sources:
        - Ledger Net Balance: Total Debits - Total Credits
        - Invoiced Balance: Sum(Invoice.balance_due) - Sum(Payment.unallocated_amount)
        Returns reconciliation status, calculated balances, and any discrepancy.
        """
        student_invoices = [inv for inv in invoices if inv.student_id == student_id and inv.status != InvoiceStatus.CANCELLED]
        student_awards = [awd for awd in awards if awd.student_id == student_id and awd.status in (ScholarshipStatus.AWARDED, ScholarshipStatus.APPLIED)]
        student_payments = [pay for pay in payments if pay.student_id == student_id and pay.status in (PaymentStatus.SETTLED, PaymentStatus.PARTIALLY_REFUNDED)]
        student_refunds = [ref for ref in refunds if ref.student_id == student_id and ref.status == RefundStatus.PROCESSED]

        total_invoiced = round(sum(inv.subtotal_amount for inv in student_invoices), 2)
        total_scholarships = round(sum(awd.award_amount for awd in student_awards), 2)
        total_payments = round(sum(pay.total_amount for pay in student_payments), 2)
        total_refunds = round(sum(ref.refund_amount for ref in student_refunds), 2)

        total_debits = round(total_invoiced + total_refunds, 2)
        total_credits = round(total_scholarships + total_payments, 2)
        ledger_net_balance = round(total_debits - total_credits, 2)

        # Invoice-level aggregate view
        invoice_outstanding_balance = round(sum(inv.balance_due for inv in student_invoices), 2)
        unallocated_cash_credits = round(sum(pay.unallocated_amount for pay in student_payments), 2)
        account_current_balance = round(invoice_outstanding_balance - unallocated_cash_credits, 2)

        # Discrepancy check
        discrepancy = round(abs(ledger_net_balance - account_current_balance), 2)
        is_reconciled = discrepancy <= 0.01

        return {
            "student_id": student_id,
            "is_reconciled": is_reconciled,
            "discrepancy": discrepancy,
            "total_invoiced": total_invoiced,
            "total_scholarships": total_scholarships,
            "total_payments": total_payments,
            "total_refunds": total_refunds,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "ledger_net_balance": ledger_net_balance,
            "invoice_outstanding_balance": invoice_outstanding_balance,
            "unallocated_cash_credits": unallocated_cash_credits,
            "account_current_balance": account_current_balance,
        }

