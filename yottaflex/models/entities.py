"""
Domain Entities for YottaFlex Student Financial System (SFS).
Defines dataclasses and validation models for all 11 core entities.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from yottaflex.models.enums import (
    ResidencyStatus,
    StudentStatus,
    DegreeLevel,
    EnrollmentStatus,
    InvoiceStatus,
    InvoiceLineType,
    ScholarshipType,
    ScholarshipStatus,
    PaymentMethod,
    PaymentStatus,
    AllocationStatus,
    RefundReason,
    RefundStatus,
    AnomalyType,
    LedgerEntryType,
)


@dataclass
class Student:
    """
    Student master entity.
    PK: student_id (STU-000001)
    """
    student_id: str
    first_name: str
    last_name: str
    email: str
    residency_status: ResidencyStatus
    program_id: str
    gpa: float
    financial_need_score: float  # 0.00 (wealthy) to 100.00 (maximum need)
    status: StudentStatus = StudentStatus.ACTIVE
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "residency_status": self.residency_status.value if isinstance(self.residency_status, ResidencyStatus) else self.residency_status,
            "program_id": self.program_id,
            "gpa": round(self.gpa, 2),
            "financial_need_score": round(self.financial_need_score, 2),
            "status": self.status.value if isinstance(self.status, StudentStatus) else self.status,
            "created_at": self.created_at,
        }


@dataclass
class Program:
    """
    Academic program entity.
    PK: program_id (PRG-001)
    """
    program_id: str
    name: str
    degree_level: DegreeLevel
    department: str
    credits_required: int
    base_tuition_per_credit: float
    mandatory_fee: float
    lab_fee_per_credit: float = 0.0
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "name": self.name,
            "degree_level": self.degree_level.value if isinstance(self.degree_level, DegreeLevel) else self.degree_level,
            "department": self.department,
            "credits_required": self.credits_required,
            "base_tuition_per_credit": round(self.base_tuition_per_credit, 2),
            "mandatory_fee": round(self.mandatory_fee, 2),
            "lab_fee_per_credit": round(self.lab_fee_per_credit, 2),
            "is_active": self.is_active,
        }


@dataclass
class FeeSchedule:
    """
    Term-specific fee schedule per program.
    PK: fee_schedule_id (FS-2026-FALL-PRG-001)
    FK: program_id -> Program
    """
    fee_schedule_id: str
    program_id: str
    term_id: str  # e.g. TERM-2026-FALL
    effective_start_date: str
    effective_end_date: str
    tuition_per_credit: float
    mandatory_fee: float
    technology_fee: float
    lab_fee_per_credit: float
    out_of_state_multiplier: float = 1.65
    international_multiplier: float = 2.10
    late_fee_amount: float = 75.00
    late_fee_grace_days: int = 14

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fee_schedule_id": self.fee_schedule_id,
            "program_id": self.program_id,
            "term_id": self.term_id,
            "effective_start_date": self.effective_start_date,
            "effective_end_date": self.effective_end_date,
            "tuition_per_credit": round(self.tuition_per_credit, 2),
            "mandatory_fee": round(self.mandatory_fee, 2),
            "technology_fee": round(self.technology_fee, 2),
            "lab_fee_per_credit": round(self.lab_fee_per_credit, 2),
            "out_of_state_multiplier": round(self.out_of_state_multiplier, 2),
            "international_multiplier": round(self.international_multiplier, 2),
            "late_fee_amount": round(self.late_fee_amount, 2),
            "late_fee_grace_days": self.late_fee_grace_days,
        }


@dataclass
class Enrollment:
    """
    Student enrollment in a program for a specific term.
    PK: enrollment_id (ENR-2026-000001)
    FK: student_id -> Student
    FK: program_id -> Program
    """
    enrollment_id: str
    student_id: str
    program_id: str
    term_id: str
    credits_enrolled: int
    enrollment_date: str
    status: EnrollmentStatus = EnrollmentStatus.CONFIRMED
    cancellation_date: Optional[str] = None
    fee_waiver_percent: float = 0.0  # 0.0 to 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enrollment_id": self.enrollment_id,
            "student_id": self.student_id,
            "program_id": self.program_id,
            "term_id": self.term_id,
            "credits_enrolled": self.credits_enrolled,
            "enrollment_date": self.enrollment_date,
            "status": self.status.value if isinstance(self.status, EnrollmentStatus) else self.status,
            "cancellation_date": self.cancellation_date,
            "fee_waiver_percent": round(self.fee_waiver_percent, 2),
        }


@dataclass
class InvoiceLine:
    """
    Itemized charge on a tuition invoice.
    PK: invoice_line_id (INVL-INV-STU-000001-2026-000001-01)
    FK: invoice_id -> Invoice
    """
    invoice_line_id: str
    invoice_id: str
    line_type: InvoiceLineType
    description: str
    unit_amount: float
    quantity: float
    line_total: float
    is_scholarship_eligible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_line_id": self.invoice_line_id,
            "invoice_id": self.invoice_id,
            "line_type": self.line_type.value if isinstance(self.line_type, InvoiceLineType) else self.line_type,
            "description": self.description,
            "unit_amount": round(self.unit_amount, 2),
            "quantity": self.quantity,
            "line_total": round(self.line_total, 2),
            "is_scholarship_eligible": self.is_scholarship_eligible,
        }


@dataclass
class Invoice:
    """
    Tuition and fee invoice for a student's term enrollment.
    PK: invoice_id (INV-STU-000001-2026-000001)
    FK: student_id -> Student
    FK: enrollment_id -> Enrollment
    """
    invoice_id: str
    student_id: str
    enrollment_id: str
    term_id: str
    issue_date: str
    due_date: str
    subtotal_amount: float
    scholarship_credit_amount: float = 0.0
    payment_credit_amount: float = 0.0
    balance_due: float = 0.0
    status: InvoiceStatus = InvoiceStatus.ISSUED
    is_duplicate: bool = False
    issue_type: Optional[str] = None  # for ground-truth anomalies

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "student_id": self.student_id,
            "enrollment_id": self.enrollment_id,
            "term_id": self.term_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "subtotal_amount": round(self.subtotal_amount, 2),
            "scholarship_credit_amount": round(self.scholarship_credit_amount, 2),
            "payment_credit_amount": round(self.payment_credit_amount, 2),
            "balance_due": round(self.balance_due, 2),
            "status": self.status.value if isinstance(self.status, InvoiceStatus) else self.status,
            "is_duplicate": self.is_duplicate,
            "issue_type": self.issue_type,
        }


@dataclass
class Scholarship:
    """
    Institutional or external scholarship program.
    PK: scholarship_id (SCH-2026-000001)
    """
    scholarship_id: str
    code: str
    name: str
    award_type: ScholarshipType
    funding_source: str
    max_award_amount: float
    min_gpa: float = 0.0
    max_financial_need: float = 100.0
    eligible_residency: Optional[str] = None  # ALL or specific residency
    covers_tuition_only: bool = True
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scholarship_id": self.scholarship_id,
            "code": self.code,
            "name": self.name,
            "award_type": self.award_type.value if isinstance(self.award_type, ScholarshipType) else self.award_type,
            "funding_source": self.funding_source,
            "max_award_amount": round(self.max_award_amount, 2),
            "min_gpa": round(self.min_gpa, 2),
            "max_financial_need": round(self.max_financial_need, 2),
            "eligible_residency": self.eligible_residency or "ALL",
            "covers_tuition_only": self.covers_tuition_only,
            "is_active": self.is_active,
        }


@dataclass
class Eligibility:
    """
    Scholarship eligibility check and actual award to a student.
    PK: award_id (AWD-2026-000001)
    FK: scholarship_id -> Scholarship
    FK: student_id -> Student
    FK: term_id
    """
    award_id: str
    scholarship_id: str
    student_id: str
    term_id: str
    award_amount: float
    eligible_amount: float
    status: ScholarshipStatus = ScholarshipStatus.AWARDED
    decision_rationale: str = ""
    evaluation_date: str = ""
    issue_type: Optional[str] = None  # e.g. SCHOLARSHIP_EXCEEDS_FEES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "award_id": self.award_id,
            "scholarship_id": self.scholarship_id,
            "student_id": self.student_id,
            "term_id": self.term_id,
            "award_amount": round(self.award_amount, 2),
            "eligible_amount": round(self.eligible_amount, 2),
            "status": self.status.value if isinstance(self.status, ScholarshipStatus) else self.status,
            "decision_rationale": self.decision_rationale,
            "evaluation_date": self.evaluation_date,
            "issue_type": self.issue_type,
        }


@dataclass
class Payment:
    """
    Payment transaction received from a student or sponsor.
    PK: payment_id (PAY-2026-000001)
    FK: student_id -> Student
    """
    payment_id: str
    student_id: str
    term_id: str
    payment_date: str
    payment_method: PaymentMethod
    total_amount: float
    allocated_amount: float = 0.0
    unallocated_amount: float = 0.0
    status: PaymentStatus = PaymentStatus.SETTLED
    transaction_reference: str = ""
    issue_type: Optional[str] = None  # e.g. PAYMENT_OVERALLOCATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "student_id": self.student_id,
            "term_id": self.term_id,
            "payment_date": self.payment_date,
            "payment_method": self.payment_method.value if isinstance(self.payment_method, PaymentMethod) else self.payment_method,
            "total_amount": round(self.total_amount, 2),
            "allocated_amount": round(self.allocated_amount, 2),
            "unallocated_amount": round(self.unallocated_amount, 2),
            "status": self.status.value if isinstance(self.status, PaymentStatus) else self.status,
            "transaction_reference": self.transaction_reference,
            "issue_type": self.issue_type,
        }


@dataclass
class PaymentAllocation:
    """
    Allocation of payment to an invoice and specific invoice line.
    PK: allocation_id (ALLOC-PAY-2026-000001-01)
    FK: payment_id -> Payment
    FK: invoice_id -> Invoice
    FK: invoice_line_id -> InvoiceLine (optional)
    """
    allocation_id: str
    payment_id: str
    invoice_id: str
    invoice_line_id: Optional[str]
    allocated_amount: float
    allocation_date: str
    status: AllocationStatus = AllocationStatus.ALLOCATED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "invoice_line_id": self.invoice_line_id or "",
            "allocated_amount": round(self.allocated_amount, 2),
            "allocation_date": self.allocation_date,
            "status": self.status.value if isinstance(self.status, AllocationStatus) else self.status,
        }


@dataclass
class Refund:
    """
    Refund issued to a student (e.g. withdrawal, overpayment).
    PK: refund_id (REF-2026-000001)
    FK: student_id -> Student
    FK: payment_id -> Payment (source payment)
    """
    refund_id: str
    student_id: str
    payment_id: str
    term_id: str
    request_date: str
    processed_date: Optional[str]
    refund_amount: float
    reason: RefundReason
    status: RefundStatus = RefundStatus.PROCESSED
    approval_notes: str = ""
    issue_type: Optional[str] = None  # e.g. REFUND_EXCEEDS_NET_PAID

    def to_dict(self) -> Dict[str, Any]:
        return {
            "refund_id": self.refund_id,
            "student_id": self.student_id,
            "payment_id": self.payment_id,
            "term_id": self.term_id,
            "request_date": self.request_date,
            "processed_date": self.processed_date or "",
            "refund_amount": round(self.refund_amount, 2),
            "reason": self.reason.value if isinstance(self.reason, RefundReason) else self.reason,
            "status": self.status.value if isinstance(self.status, RefundStatus) else self.status,
            "approval_notes": self.approval_notes,
            "issue_type": self.issue_type,
        }


@dataclass
class StudentLedgerEntry:
    """
    Double-entry accounting transaction record for auditability.
    PK: entry_id (LED-2026-000001)
    FK: student_id -> Student
    """
    entry_id: str
    student_id: str
    term_id: str
    transaction_date: str
    entry_type: LedgerEntryType  # DEBIT (+ owes) or CREDIT (- owes)
    source_entity_type: str      # INVOICE, SCHOLARSHIP, PAYMENT, REFUND, LATE_FEE
    source_entity_id: str        # e.g. INV-..., PAY-...
    amount: float
    running_balance: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "student_id": self.student_id,
            "term_id": self.term_id,
            "transaction_date": self.transaction_date,
            "entry_type": self.entry_type.value if isinstance(self.entry_type, LedgerEntryType) else self.entry_type,
            "source_entity_type": self.source_entity_type,
            "source_entity_id": self.source_entity_id,
            "amount": round(self.amount, 2),
            "running_balance": round(self.running_balance, 2),
            "description": self.description,
        }

