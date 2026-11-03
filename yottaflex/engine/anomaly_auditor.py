"""
Rule Exception and Financial Anomaly Auditor.
Detects edge cases across financial transactions and benchmarks detection accuracy against ground truth.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from yottaflex.models.enums import (
    AnomalyType,
    InvoiceStatus,
    PaymentStatus,
    RefundStatus,
    ScholarshipStatus,
    InvoiceLineType,
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
from yottaflex.engine.ledger_reconciler import LedgerReconciler


class AnomalyAuditor:
    """
    Audits financial datasets against the 5 key business rule violations and reports metrics.
    """

    @classmethod
    def audit_all(
        cls,
        students: List[Student],
        invoices: List[Invoice],
        invoice_lines: List[InvoiceLine],
        awards: List[Eligibility],
        payments: List[Payment],
        allocations: List[PaymentAllocation],
        refunds: List[Refund],
    ) -> List[Dict[str, Any]]:
        """
        Executes comprehensive audit rules across all financial records.
        Returns a list of detected anomalies with root-cause explanations and entity references.
        """
        detected: List[Dict[str, Any]] = []

        # Index lines by invoice_id
        lines_by_inv = defaultdict(list)
        for line in invoice_lines:
            lines_by_inv[line.invoice_id].append(line)

        # Index allocations by payment_id
        allocs_by_payment = defaultdict(list)
        for alloc in allocations:
            allocs_by_payment[alloc.payment_id].append(alloc)

        # -------------------------------------------------------------
        # Rule 1: Payment Allocated Beyond Amount
        # -------------------------------------------------------------
        for pay in payments:
            pay_allocs = allocs_by_payment.get(pay.payment_id, [])
            total_allocated = round(sum(a.allocated_amount for a in pay_allocs), 2)
            if total_allocated > round(pay.total_amount + 0.01, 2) or round(pay.allocated_amount, 2) > round(pay.total_amount + 0.01, 2):
                over_amount = round(max(total_allocated, pay.allocated_amount) - pay.total_amount, 2)
                detected.append({
                    "anomaly_type": AnomalyType.PAYMENT_OVERALLOCATION.value,
                    "entity_type": "Payment",
                    "entity_id": pay.payment_id,
                    "student_id": pay.student_id,
                    "description": f"Payment {pay.payment_id} total is ${pay.total_amount:.2f}, but allocated sum is ${total_allocated:.2f} (over-allocated by ${over_amount:.2f}).",
                    "severity": "HIGH",
                })

        # -------------------------------------------------------------
        # Rule 2: Scholarship Exceeds Eligible Fees
        # -------------------------------------------------------------
        invoices_by_student_term = defaultdict(list)
        for inv in invoices:
            if inv.status != InvoiceStatus.CANCELLED:
                invoices_by_student_term[(inv.student_id, inv.term_id)].append(inv)

        for awd in awards:
            if awd.status in (ScholarshipStatus.AWARDED, ScholarshipStatus.APPLIED):
                matching_invoices = invoices_by_student_term.get((awd.student_id, awd.term_id), [])
                eligible_fees = 0.0
                for inv in matching_invoices:
                    lines = lines_by_inv.get(inv.invoice_id, [])
                    eligible_fees += sum(
                        max(0.0, l.line_total) for l in lines
                        if l.line_type == InvoiceLineType.TUITION or l.is_scholarship_eligible
                    )
                eligible_fees = round(eligible_fees, 2)

                if awd.award_amount > round(eligible_fees + 0.01, 2):
                    excess = round(awd.award_amount - eligible_fees, 2)
                    detected.append({
                        "anomaly_type": AnomalyType.SCHOLARSHIP_EXCEEDS_FEES.value,
                        "entity_type": "Eligibility",
                        "entity_id": awd.award_id,
                        "student_id": awd.student_id,
                        "description": f"Scholarship award {awd.award_id} of ${awd.award_amount:.2f} exceeds eligible fee cap of ${eligible_fees:.2f} by ${excess:.2f}.",
                        "severity": "HIGH",
                    })

        # -------------------------------------------------------------
        # Rule 3: Invoice Generated Twice (Duplicate Invoices)
        # -------------------------------------------------------------
        seen_invoices = {}
        for inv in invoices:
            if inv.status == InvoiceStatus.CANCELLED:
                continue
            key = (inv.student_id, inv.term_id, inv.enrollment_id)
            if key in seen_invoices:
                orig_inv_id = seen_invoices[key]
                detected.append({
                    "anomaly_type": AnomalyType.DUPLICATE_INVOICE.value,
                    "entity_type": "Invoice",
                    "entity_id": inv.invoice_id,
                    "student_id": inv.student_id,
                    "description": f"Duplicate invoice {inv.invoice_id} detected for Student {inv.student_id}, Term {inv.term_id}, Enrollment {inv.enrollment_id} (Original: {orig_inv_id}).",
                    "severity": "MEDIUM",
                })
            else:
                seen_invoices[key] = inv.invoice_id

        # -------------------------------------------------------------
        # Rule 4: Refund Exceeds Net Paid
        # -------------------------------------------------------------
        payments_by_student = defaultdict(list)
        for p in payments:
            if p.status in (PaymentStatus.SETTLED, PaymentStatus.PARTIALLY_REFUNDED, PaymentStatus.REFUNDED):
                payments_by_student[p.student_id].append(p)

        refunds_by_student = defaultdict(list)
        for r in refunds:
            refunds_by_student[r.student_id].append(r)

        for student_id, student_refund_list in refunds_by_student.items():
            stu_payments = payments_by_student.get(student_id, [])
            total_settled_cash = sum(p.total_amount for p in stu_payments)
            cumulative_refunds = 0.0

            for ref in student_refund_list:
                cumulative_refunds = round(cumulative_refunds + ref.refund_amount, 2)
                if cumulative_refunds > round(total_settled_cash + 0.01, 2):
                    excess = round(cumulative_refunds - total_settled_cash, 2)
                    detected.append({
                        "anomaly_type": AnomalyType.REFUND_EXCEEDS_NET_PAID.value,
                        "entity_type": "Refund",
                        "entity_id": ref.refund_id,
                        "student_id": student_id,
                        "description": f"Refund {ref.refund_id} of ${ref.refund_amount:.2f} brings total refunded to ${cumulative_refunds:.2f}, exceeding settled payments of ${total_settled_cash:.2f} by ${excess:.2f}.",
                        "severity": "CRITICAL",
                    })

        # -------------------------------------------------------------
        # Rule 5: Balance Disagrees with Ledger (Root Cause Isolation)
        # -------------------------------------------------------------
        # Exclude students who already have primary transaction anomalies,
        # isolating students with unexplained balance corruptions.
        upstream_students = {
            d["student_id"] for d in detected
            if d["anomaly_type"] in (
                AnomalyType.PAYMENT_OVERALLOCATION.value,
                AnomalyType.SCHOLARSHIP_EXCEEDS_FEES.value,
                AnomalyType.DUPLICATE_INVOICE.value,
                AnomalyType.REFUND_EXCEEDS_NET_PAID.value,
            )
        }

        student_ids = {s.student_id for s in students}
        for stu_id in student_ids:
            if stu_id in upstream_students:
                continue

            recon = LedgerReconciler.reconcile_student(
                student_id=stu_id,
                invoices=invoices,
                awards=awards,
                payments=payments,
                refunds=refunds,
            )
            if not recon["is_reconciled"]:
                detected.append({
                    "anomaly_type": AnomalyType.BALANCE_LEDGER_DISCREPANCY.value,
                    "entity_type": "Student",
                    "entity_id": stu_id,
                    "student_id": stu_id,
                    "description": f"Student {stu_id} reported balance (${recon['account_current_balance']:.2f}) disagrees with general ledger net balance (${recon['ledger_net_balance']:.2f}) by ${recon['discrepancy']:.2f}.",
                    "severity": "HIGH",
                })

        return detected

    @classmethod
    def evaluate_against_ground_truth(
        cls,
        detected_anomalies: List[Dict[str, Any]],
        ground_truth: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Computes detection performance metrics (Precision, Recall, F1, TP, FP, FN)
        by anomaly type and overall.
        """
        gt_keys: Set[Tuple[str, str]] = {
            (gt["anomaly_type"], gt["entity_id"]) for gt in ground_truth
        }
        det_keys: Set[Tuple[str, str]] = {
            (det["anomaly_type"], det["entity_id"]) for det in detected_anomalies
        }

        tp = len(gt_keys.intersection(det_keys))
        fp = len(det_keys - gt_keys)
        fn = len(gt_keys - det_keys)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        categories = [
            AnomalyType.PAYMENT_OVERALLOCATION.value,
            AnomalyType.SCHOLARSHIP_EXCEEDS_FEES.value,
            AnomalyType.DUPLICATE_INVOICE.value,
            AnomalyType.REFUND_EXCEEDS_NET_PAID.value,
            AnomalyType.BALANCE_LEDGER_DISCREPANCY.value,
        ]

        breakdown = {}
        for cat in categories:
            cat_gt = {k for k in gt_keys if k[0] == cat}
            cat_det = {k for k in det_keys if k[0] == cat}
            c_tp = len(cat_gt.intersection(cat_det))
            c_fp = len(cat_det - cat_gt)
            c_fn = len(cat_gt - cat_det)
            c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 1.0
            c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 1.0
            c_f1 = (2 * c_prec * c_rec) / (c_prec + c_rec) if (c_prec + c_rec) > 0 else 0.0
            breakdown[cat] = {
                "ground_truth_count": len(cat_gt),
                "detected_count": len(cat_det),
                "true_positives": c_tp,
                "false_positives": c_fp,
                "false_negatives": c_fn,
                "precision": round(c_prec, 4),
                "recall": round(c_rec, 4),
                "f1_score": round(c_f1, 4),
            }

        return {
            "overall": {
                "ground_truth_total": len(ground_truth),
                "detected_total": len(detected_anomalies),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            },
            "by_category": breakdown,
        }
