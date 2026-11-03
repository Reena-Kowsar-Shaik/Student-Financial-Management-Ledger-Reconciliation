"""
Labelled Edge Case Injectors for YottaFlex Synthetic Data Generation.
Injects the 5 required anomalous scenarios with explicit ground-truth tracking and student isolation.
"""

from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
from yottaflex.models.enums import (
    AnomalyType,
    InvoiceStatus,
    PaymentStatus,
    RefundStatus,
    RefundReason,
    AllocationStatus,
)
from yottaflex.models.entities import (
    Student,
    Invoice,
    InvoiceLine,
    Eligibility,
    Payment,
    PaymentAllocation,
    Refund,
)


class EdgeCaseInjector:
    """
    Injects deterministic, controlled edge cases into the baseline dataset
    and outputs ground-truth labels decoupled from model features.
    """

    @classmethod
    def inject_all_edge_cases(
        cls,
        invoices: List[Invoice],
        invoice_lines: List[InvoiceLine],
        awards: List[Eligibility],
        payments: List[Payment],
        allocations: List[PaymentAllocation],
        refunds: List[Refund],
        students: List[Student],
        count_per_type: int = 5,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Injects the 5 required anomaly patterns in an isolated, deterministic manner.
        Returns: (ground_truth_records, updated_entity_collections)
        """
        ground_truth: List[Dict[str, Any]] = []
        assigned_students: Set[str] = set()

        # Group entities by student for clean partition
        payments_by_stu = defaultdict(list)
        for p in payments:
            payments_by_stu[p.student_id].append(p)

        awards_by_stu = defaultdict(list)
        for a in awards:
            awards_by_stu[a.student_id].append(a)

        invoices_by_stu = defaultdict(list)
        for inv in invoices:
            invoices_by_stu[inv.student_id].append(inv)

        allocs_by_payment = defaultdict(list)
        for al in allocations:
            allocs_by_payment[al.payment_id].append(al)

        # -------------------------------------------------------------
        # Anomaly 1: Payment Allocated Beyond Amount
        # -------------------------------------------------------------
        eligible_pay_candidates = [
            p for p in payments
            if p.allocated_amount > 0 and p.student_id not in assigned_students
        ]
        injected_pay_count = 0
        for target_payment in eligible_pay_candidates:
            if injected_pay_count >= count_per_type:
                break
            target_allocs = allocs_by_payment.get(target_payment.payment_id, [])
            if target_allocs:
                excess = 500.00
                new_alloc_id = f"ALLOC-{target_payment.payment_id}-ERR"
                err_alloc = PaymentAllocation(
                    allocation_id=new_alloc_id,
                    payment_id=target_payment.payment_id,
                    invoice_id=target_allocs[0].invoice_id,
                    invoice_line_id=target_allocs[0].invoice_line_id,
                    allocated_amount=excess,
                    allocation_date=target_payment.payment_date,
                    status=AllocationStatus.ALLOCATED,
                )
                allocations.append(err_alloc)
                target_payment.allocated_amount = round(target_payment.allocated_amount + excess, 2)
                target_payment.issue_type = AnomalyType.PAYMENT_OVERALLOCATION.value

                ground_truth.append({
                    "ground_truth_id": f"GT-ERR-1-{injected_pay_count+1:03d}",
                    "anomaly_type": AnomalyType.PAYMENT_OVERALLOCATION.value,
                    "entity_type": "Payment",
                    "entity_id": target_payment.payment_id,
                    "student_id": target_payment.student_id,
                    "expected_rule": "Payment allocated amount must be <= total payment amount",
                    "actual_value": f"Total: ${target_payment.total_amount:.2f}, Allocated: ${target_payment.allocated_amount:.2f}",
                    "severity": "HIGH",
                })
                assigned_students.add(target_payment.student_id)
                injected_pay_count += 1

        # -------------------------------------------------------------
        # Anomaly 2: Scholarship Exceeds Eligible Fees
        # -------------------------------------------------------------
        eligible_award_candidates = [
            a for a in awards
            if a.award_amount > 0 and a.student_id not in assigned_students
        ]
        injected_award_count = 0
        for target_award in eligible_award_candidates:
            if injected_award_count >= count_per_type:
                break
            excess_amount = 4500.00
            target_award.award_amount = round(target_award.eligible_amount + excess_amount, 2)
            target_award.issue_type = AnomalyType.SCHOLARSHIP_EXCEEDS_FEES.value

            ground_truth.append({
                "ground_truth_id": f"GT-ERR-2-{injected_award_count+1:03d}",
                "anomaly_type": AnomalyType.SCHOLARSHIP_EXCEEDS_FEES.value,
                "entity_type": "Eligibility",
                "entity_id": target_award.award_id,
                "student_id": target_award.student_id,
                "expected_rule": "Scholarship award amount cannot exceed eligible tuition/fees",
                "actual_value": f"Eligible: ${target_award.eligible_amount:.2f}, Awarded: ${target_award.award_amount:.2f}",
                "severity": "HIGH",
            })
            assigned_students.add(target_award.student_id)
            injected_award_count += 1

        # -------------------------------------------------------------
        # Anomaly 3: Invoice Generated Twice (Duplicate Invoices)
        # -------------------------------------------------------------
        eligible_inv_candidates = [
            inv for inv in invoices
            if inv.status == InvoiceStatus.ISSUED and inv.student_id not in assigned_students
        ]
        injected_inv_count = 0
        for orig_inv in eligible_inv_candidates:
            if injected_inv_count >= count_per_type:
                break
            dup_id = f"INV-DUP-{orig_inv.invoice_id}"
            dup_inv = Invoice(
                invoice_id=dup_id,
                student_id=orig_inv.student_id,
                enrollment_id=orig_inv.enrollment_id,
                term_id=orig_inv.term_id,
                issue_date=orig_inv.issue_date,
                due_date=orig_inv.due_date,
                subtotal_amount=orig_inv.subtotal_amount,
                scholarship_credit_amount=0.0,
                payment_credit_amount=0.0,
                balance_due=orig_inv.subtotal_amount,
                status=InvoiceStatus.ISSUED,
                is_duplicate=True,
                issue_type=AnomalyType.DUPLICATE_INVOICE.value,
            )
            invoices.append(dup_inv)

            # Duplicate associated invoice lines
            orig_lines = [l for l in invoice_lines if l.invoice_id == orig_inv.invoice_id]
            for ln_idx, ol in enumerate(orig_lines, start=1):
                dup_line = InvoiceLine(
                    invoice_line_id=f"INVL-{dup_id}-{ln_idx:02d}",
                    invoice_id=dup_id,
                    line_type=ol.line_type,
                    description=f"{ol.description} (Duplicate)",
                    unit_amount=ol.unit_amount,
                    quantity=ol.quantity,
                    line_total=ol.line_total,
                    is_scholarship_eligible=ol.is_scholarship_eligible,
                )
                invoice_lines.append(dup_line)

            ground_truth.append({
                "ground_truth_id": f"GT-ERR-3-{injected_inv_count+1:03d}",
                "anomaly_type": AnomalyType.DUPLICATE_INVOICE.value,
                "entity_type": "Invoice",
                "entity_id": dup_id,
                "student_id": orig_inv.student_id,
                "expected_rule": "Only one active invoice per enrollment and term is permitted",
                "actual_value": f"Duplicate invoice {dup_id} generated alongside {orig_inv.invoice_id}",
                "severity": "MEDIUM",
            })
            assigned_students.add(orig_inv.student_id)
            injected_inv_count += 1

        # -------------------------------------------------------------
        # Anomaly 4: Refund Exceeds Net Paid
        # -------------------------------------------------------------
        candidate_refund_students = [
            s.student_id for s in students
            if s.student_id not in assigned_students and len(payments_by_stu.get(s.student_id, [])) > 0
        ]
        injected_ref_count = 0
        for sid in candidate_refund_students:
            if injected_ref_count >= count_per_type:
                break
            stu_payments = payments_by_stu[sid]
            total_settled_cash = round(sum(p.total_amount for p in stu_payments), 2)
            excess_refund = round(total_settled_cash + 1500.00, 2)
            ref_id = f"REF-ERR-{injected_ref_count+1:03d}"
            primary_pay = stu_payments[0]

            unauthorized_refund = Refund(
                refund_id=ref_id,
                student_id=sid,
                payment_id=primary_pay.payment_id,
                term_id=primary_pay.term_id,
                request_date="2026-10-15",
                processed_date="2026-10-16",
                refund_amount=excess_refund,
                reason=RefundReason.ERROR_CORRECTION,
                status=RefundStatus.PROCESSED,
                approval_notes="Anomalous refund exceeding total settled payments.",
                issue_type=AnomalyType.REFUND_EXCEEDS_NET_PAID.value,
            )
            refunds.append(unauthorized_refund)

            ground_truth.append({
                "ground_truth_id": f"GT-ERR-4-{injected_ref_count+1:03d}",
                "anomaly_type": AnomalyType.REFUND_EXCEEDS_NET_PAID.value,
                "entity_type": "Refund",
                "entity_id": ref_id,
                "student_id": sid,
                "expected_rule": "Refund amount cannot exceed net settled payments",
                "actual_value": f"Settled: ${total_settled_cash:.2f}, Refunded: ${excess_refund:.2f}",
                "severity": "CRITICAL",
            })
            assigned_students.add(sid)
            injected_ref_count += 1

        # -------------------------------------------------------------
        # Anomaly 5: Balance Disagrees with Ledger
        # -------------------------------------------------------------
        candidate_bal_students = [
            s for s in students
            if s.student_id not in assigned_students
        ]
        injected_bal_count = 0
        for stu in candidate_bal_students:
            if injected_bal_count >= count_per_type:
                break
            stu_invoices = [inv for inv in invoices_by_stu.get(stu.student_id, []) if inv.balance_due > 0]
            if stu_invoices:
                corrupted_inv = stu_invoices[0]
                phantom_discount = 850.00
                corrupted_inv.balance_due = round(max(0.0, corrupted_inv.balance_due - phantom_discount), 2)
                corrupted_inv.issue_type = AnomalyType.BALANCE_LEDGER_DISCREPANCY.value

                ground_truth.append({
                    "ground_truth_id": f"GT-ERR-5-{injected_bal_count+1:03d}",
                    "anomaly_type": AnomalyType.BALANCE_LEDGER_DISCREPANCY.value,
                    "entity_type": "Student",
                    "entity_id": stu.student_id,
                    "student_id": stu.student_id,
                    "expected_rule": "Student invoice balances must equal double-entry ledger net balance",
                    "actual_value": f"Corrupted balance on invoice {corrupted_inv.invoice_id} creating discrepancy",
                    "severity": "HIGH",
                })
                assigned_students.add(stu.student_id)
                injected_bal_count += 1

        return ground_truth, {
            "invoices": invoices,
            "invoice_lines": invoice_lines,
            "awards": awards,
            "payments": payments,
            "allocations": allocations,
            "refunds": refunds,
        }
