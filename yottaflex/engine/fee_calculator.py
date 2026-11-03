"""
Tuition and Fee Calculation Engine.
Calculates itemized tuition, mandatory fees, course/lab fees, waivers, and late fees.
"""

from typing import List, Tuple
from datetime import datetime, date, timedelta
from yottaflex.models.enums import (
    ResidencyStatus,
    InvoiceStatus,
    InvoiceLineType,
)
from yottaflex.models.entities import (
    Student,
    Program,
    FeeSchedule,
    Enrollment,
    Invoice,
    InvoiceLine,
)


class FeeCalculator:
    """
    Computes tuition charges, mandatory/optional fees, waivers, and late penalties.
    """

    @staticmethod
    def calculate_tuition_rate(fee_schedule: FeeSchedule, residency: ResidencyStatus) -> float:
        """
        Determines the per-credit tuition rate based on student residency status.
        """
        base_rate = fee_schedule.tuition_per_credit
        if residency == ResidencyStatus.IN_STATE:
            return round(base_rate, 2)
        elif residency == ResidencyStatus.OUT_OF_STATE:
            return round(base_rate * fee_schedule.out_of_state_multiplier, 2)
        elif residency == ResidencyStatus.INTERNATIONAL:
            return round(base_rate * fee_schedule.international_multiplier, 2)
        return round(base_rate, 2)

    @classmethod
    def generate_invoice(
        cls,
        invoice_id: str,
        student: Student,
        program: Program,
        fee_schedule: FeeSchedule,
        enrollment: Enrollment,
        issue_date: str,
        due_days: int = 30,
    ) -> Tuple[Invoice, List[InvoiceLine]]:
        """
        Calculates all line items and produces an Invoice with associated InvoiceLines.
        """
        # Determine due date
        issue_dt = datetime.strptime(issue_date, "%Y-%m-%d").date()
        due_dt = issue_dt + timedelta(days=due_days)
        due_date_str = due_dt.strftime("%Y-%m-%d")

        effective_rate = cls.calculate_tuition_rate(fee_schedule, student.residency_status)
        credits = enrollment.credits_enrolled
        tuition_total = round(effective_rate * credits, 2)

        lines: List[InvoiceLine] = []
        line_num = 1

        # 1. Tuition Line
        lines.append(
            InvoiceLine(
                invoice_line_id=f"INVL-{invoice_id}-{line_num:02d}",
                invoice_id=invoice_id,
                line_type=InvoiceLineType.TUITION,
                description=f"Tuition ({credits} credits @ ${effective_rate:.2f}/credit - {student.residency_status.value})",
                unit_amount=effective_rate,
                quantity=float(credits),
                line_total=tuition_total,
                is_scholarship_eligible=True,
            )
        )
        line_num += 1

        # 2. Mandatory Student Services Fee
        if fee_schedule.mandatory_fee > 0:
            lines.append(
                InvoiceLine(
                    invoice_line_id=f"INVL-{invoice_id}-{line_num:02d}",
                    invoice_id=invoice_id,
                    line_type=InvoiceLineType.MANDATORY_FEE,
                    description=f"Mandatory Student Services Fee ({fee_schedule.term_id})",
                    unit_amount=round(fee_schedule.mandatory_fee, 2),
                    quantity=1.0,
                    line_total=round(fee_schedule.mandatory_fee, 2),
                    is_scholarship_eligible=False,  # by default institutional scholarships only cover tuition
                )
            )
            line_num += 1

        # 3. Technology Fee
        if fee_schedule.technology_fee > 0:
            lines.append(
                InvoiceLine(
                    invoice_line_id=f"INVL-{invoice_id}-{line_num:02d}",
                    invoice_id=invoice_id,
                    line_type=InvoiceLineType.MANDATORY_FEE,
                    description="Campus Technology & Infrastructure Fee",
                    unit_amount=round(fee_schedule.technology_fee, 2),
                    quantity=1.0,
                    line_total=round(fee_schedule.technology_fee, 2),
                    is_scholarship_eligible=False,
                )
            )
            line_num += 1

        # 4. Lab / Specialized Course Fee (if applicable)
        if fee_schedule.lab_fee_per_credit > 0:
            lab_total = round(fee_schedule.lab_fee_per_credit * credits, 2)
            lines.append(
                InvoiceLine(
                    invoice_line_id=f"INVL-{invoice_id}-{line_num:02d}",
                    invoice_id=invoice_id,
                    line_type=InvoiceLineType.LAB_FEE,
                    description=f"Specialized Lab & Materials Fee ({credits} credits @ ${fee_schedule.lab_fee_per_credit:.2f})",
                    unit_amount=round(fee_schedule.lab_fee_per_credit, 2),
                    quantity=float(credits),
                    line_total=lab_total,
                    is_scholarship_eligible=False,
                )
            )
            line_num += 1

        # 5. Fee Waiver (Negative line item if student has approved waiver)
        if enrollment.fee_waiver_percent > 0:
            waiver_pct = min(100.0, max(0.0, enrollment.fee_waiver_percent))
            waiver_discount = round(tuition_total * (waiver_pct / 100.0), 2)
            lines.append(
                InvoiceLine(
                    invoice_line_id=f"INVL-{invoice_id}-{line_num:02d}",
                    invoice_id=invoice_id,
                    line_type=InvoiceLineType.FEE_WAIVER,
                    description=f"Approved Academic Fee Waiver ({waiver_pct:.1f}% on tuition)",
                    unit_amount=-waiver_discount,
                    quantity=1.0,
                    line_total=-waiver_discount,
                    is_scholarship_eligible=False,
                )
            )
            line_num += 1

        subtotal = round(sum(l.line_total for l in lines), 2)

        invoice = Invoice(
            invoice_id=invoice_id,
            student_id=student.student_id,
            enrollment_id=enrollment.enrollment_id,
            term_id=fee_schedule.term_id,
            issue_date=issue_date,
            due_date=due_date_str,
            subtotal_amount=subtotal,
            scholarship_credit_amount=0.0,
            payment_credit_amount=0.0,
            balance_due=subtotal,
            status=InvoiceStatus.ISSUED,
        )

        return invoice, lines

    @classmethod
    def assess_late_fee(
        cls,
        invoice: Invoice,
        lines: List[InvoiceLine],
        fee_schedule: FeeSchedule,
        as_of_date: str,
    ) -> bool:
        """
        Assesses a late fee if the invoice has an outstanding balance after the grace period.
        Returns True if a late fee was added, False otherwise.
        """
        if invoice.balance_due <= 0 or invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
            return False

        due_dt = datetime.strptime(invoice.due_date, "%Y-%m-%d").date()
        as_of_dt = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        grace_dt = due_dt + timedelta(days=fee_schedule.late_fee_grace_days)

        if as_of_dt > grace_dt:
            # Check if late fee already assessed
            has_late_fee = any(l.line_type == InvoiceLineType.LATE_FEE for l in lines)
            if not has_late_fee and fee_schedule.late_fee_amount > 0:
                line_num = len(lines) + 1
                late_line = InvoiceLine(
                    invoice_line_id=f"INVL-{invoice.invoice_id}-{line_num:02d}",
                    invoice_id=invoice.invoice_id,
                    line_type=InvoiceLineType.LATE_FEE,
                    description=f"Late Payment Penalty (Past due +{fee_schedule.late_fee_grace_days}d grace)",
                    unit_amount=fee_schedule.late_fee_amount,
                    quantity=1.0,
                    line_total=round(fee_schedule.late_fee_amount, 2),
                    is_scholarship_eligible=False,
                )
                lines.append(late_line)
                invoice.subtotal_amount = round(invoice.subtotal_amount + fee_schedule.late_fee_amount, 2)
                invoice.balance_due = round(invoice.balance_due + fee_schedule.late_fee_amount, 2)
                invoice.status = InvoiceStatus.OVERDUE
                return True
        return False

