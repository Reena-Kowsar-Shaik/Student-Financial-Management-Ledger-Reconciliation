"""
Domain Enums for YottaFlex Student Financial System (SFS).
"""

from enum import Enum


class ResidencyStatus(str, Enum):
    IN_STATE = "IN_STATE"
    OUT_OF_STATE = "OUT_OF_STATE"
    INTERNATIONAL = "INTERNATIONAL"


class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    WITHDRAWN = "WITHDRAWN"
    GRADUATED = "GRADUATED"


class DegreeLevel(str, Enum):
    UNDERGRADUATE = "UNDERGRADUATE"
    GRADUATE = "GRADUATE"
    DOCTORAL = "DOCTORAL"


class EnrollmentStatus(str, Enum):
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class InvoiceLineType(str, Enum):
    TUITION = "TUITION"
    MANDATORY_FEE = "MANDATORY_FEE"
    LAB_FEE = "LAB_FEE"
    LATE_FEE = "LATE_FEE"
    FEE_WAIVER = "FEE_WAIVER"


class ScholarshipType(str, Enum):
    MERIT = "MERIT"
    NEED_BASED = "NEED_BASED"
    ATHLETIC = "ATHLETIC"
    DEPARTMENTAL = "DEPARTMENTAL"
    TUITION_WAIVER = "TUITION_WAIVER"


class ScholarshipStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    AWARDED = "AWARDED"
    APPLIED = "APPLIED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    ACH_TRANSFER = "ACH_TRANSFER"
    WIRE = "WIRE"
    THIRD_PARTY = "THIRD_PARTY"
    CASH = "CASH"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class AllocationStatus(str, Enum):
    ALLOCATED = "ALLOCATED"
    REVERSED = "REVERSED"


class RefundReason(str, Enum):
    WITHDRAWAL = "WITHDRAWAL"
    OVERPAYMENT = "OVERPAYMENT"
    WAIVER_ADJUSTMENT = "WAIVER_ADJUSTMENT"
    ERROR_CORRECTION = "ERROR_CORRECTION"


class RefundStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class AnomalyType(str, Enum):
    PAYMENT_OVERALLOCATION = "PAYMENT_OVERALLOCATION"
    SCHOLARSHIP_EXCEEDS_FEES = "SCHOLARSHIP_EXCEEDS_FEES"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    REFUND_EXCEEDS_NET_PAID = "REFUND_EXCEEDS_NET_PAID"
    BALANCE_LEDGER_DISCREPANCY = "BALANCE_LEDGER_DISCREPANCY"


class LedgerEntryType(str, Enum):
    DEBIT = "DEBIT"    # Increases student obligation (Tuition, Late Fee, Refund)
    CREDIT = "CREDIT"  # Decreases student obligation (Payment, Scholarship, Waiver)
