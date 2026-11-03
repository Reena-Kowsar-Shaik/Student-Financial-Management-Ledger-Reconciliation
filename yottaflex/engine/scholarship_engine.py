"""
Scholarship Eligibility and Award Engine.
Evaluates student eligibility, determines net eligible fee caps (accounting for waivers), and applies awards.
"""

from typing import List, Optional, Tuple
from yottaflex.models.enums import (
    ScholarshipType,
    ScholarshipStatus,
    InvoiceStatus,
    InvoiceLineType,
)
from yottaflex.models.entities import (
    Student,
    Scholarship,
    Eligibility,
    Invoice,
    InvoiceLine,
)


class ScholarshipEngine:
    """
    Evaluates scholarship eligibility rules and safely awards funding against net tuition/fee lines.
    """

    @staticmethod
    def calculate_eligible_amount(
        scholarship: Scholarship,
        invoice_lines: List[InvoiceLine],
    ) -> float:
        """
        Calculates the maximum charge amount eligible for this scholarship.
        Accounts for fee waivers that reduce net tuition obligations.
        """
        eligible_sum = 0.0
        waiver_sum = 0.0

        for line in invoice_lines:
            if line.line_type == InvoiceLineType.FEE_WAIVER:
                waiver_sum += abs(line.line_total)
            elif scholarship.covers_tuition_only:
                if line.line_type == InvoiceLineType.TUITION:
                    eligible_sum += max(0.0, line.line_total)
            else:
                if line.is_scholarship_eligible or line.line_type == InvoiceLineType.TUITION:
                    eligible_sum += max(0.0, line.line_total)

        # Subtract fee waiver discount from eligible tuition
        net_eligible = max(0.0, eligible_sum - waiver_sum)
        return round(net_eligible, 2)

    @classmethod
    def evaluate_eligibility(
        cls,
        award_id: str,
        student: Student,
        scholarship: Scholarship,
        term_id: str,
        invoice_lines: List[InvoiceLine],
        evaluation_date: str,
    ) -> Eligibility:
        """
        Determines eligibility and computes the awarded amount.
        Enforces that scholarship awards cannot exceed net eligible fees.
        """
        rejection_reasons = []

        # 1. Check GPA
        if scholarship.min_gpa > 0 and student.gpa < scholarship.min_gpa:
            rejection_reasons.append(
                f"GPA {student.gpa:.2f} is below minimum requirement of {scholarship.min_gpa:.2f}"
            )

        # 2. Check Financial Need (if need-based)
        if scholarship.award_type == ScholarshipType.NEED_BASED:
            if student.financial_need_score < 40.0:
                rejection_reasons.append(
                    f"Financial need score {student.financial_need_score:.1f} does not meet need criteria (>= 40.0)"
                )

        # 3. Check Residency
        if scholarship.eligible_residency and scholarship.eligible_residency != "ALL":
            if student.residency_status.value != scholarship.eligible_residency:
                rejection_reasons.append(
                    f"Residency {student.residency_status.value} does not match required {scholarship.eligible_residency}"
                )

        # 4. Check Eligible Charges
        eligible_fees = cls.calculate_eligible_amount(scholarship, invoice_lines)
        if eligible_fees <= 0:
            rejection_reasons.append("No eligible tuition or fee charges found on invoice")

        if rejection_reasons:
            return Eligibility(
                award_id=award_id,
                scholarship_id=scholarship.scholarship_id,
                student_id=student.student_id,
                term_id=term_id,
                award_amount=0.0,
                eligible_amount=eligible_fees,
                status=ScholarshipStatus.REJECTED,
                decision_rationale="; ".join(rejection_reasons),
                evaluation_date=evaluation_date,
            )

        # Safe Award Amount: min of scholarship cap and net eligible charges
        award_amount = round(min(scholarship.max_award_amount, eligible_fees), 2)
        rationale = (
            f"Approved: GPA {student.gpa:.2f} >= {scholarship.min_gpa:.2f}. "
            f"Net eligible fees: ${eligible_fees:.2f}. Award capped at ${award_amount:.2f}."
        )

        return Eligibility(
            award_id=award_id,
            scholarship_id=scholarship.scholarship_id,
            student_id=student.student_id,
            term_id=term_id,
            award_amount=award_amount,
            eligible_amount=eligible_fees,
            status=ScholarshipStatus.AWARDED,
            decision_rationale=rationale,
            evaluation_date=evaluation_date,
        )

    @staticmethod
    def apply_award_to_invoice(
        award: Eligibility,
        invoice: Invoice,
    ) -> None:
        """
        Applies an awarded scholarship as a credit against an invoice.
        Enforces that the award applied cannot exceed the current invoice balance.
        """
        if award.status not in (ScholarshipStatus.AWARDED, ScholarshipStatus.APPLIED):
            return

        # Ensure award doesn't exceed invoice balance
        applied_amount = round(min(award.award_amount, invoice.balance_due), 2)
        award.award_amount = applied_amount

        invoice.scholarship_credit_amount = round(invoice.scholarship_credit_amount + applied_amount, 2)
        invoice.balance_due = round(max(0.0, invoice.subtotal_amount - invoice.scholarship_credit_amount - invoice.payment_credit_amount), 2)
        award.status = ScholarshipStatus.APPLIED

        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
        elif invoice.scholarship_credit_amount > 0 or invoice.payment_credit_amount > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
