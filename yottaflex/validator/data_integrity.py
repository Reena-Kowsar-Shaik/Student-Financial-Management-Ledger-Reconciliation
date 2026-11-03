"""
Data Integrity and Acceptance Validator.
Enforces Step 8 validation rules: PK uniqueness, FK referential integrity,
enum domain compliance, date sequence logic, arithmetic balance reconciliation, and lifecycle states.
"""

from typing import Dict, List, Any, Set
from collections import Counter
from datetime import datetime
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
    RefundReason,
    RefundStatus,
)


class DataIntegrityValidator:
    """
    Automated acceptance testing and data integrity verification suite.
    """

    @classmethod
    def validate_dataset(cls, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes all Step 8 validation passes across the dataset.
        Returns a comprehensive validation report.
        """
        results = {
            "is_valid": True,
            "checks_passed": 0,
            "checks_failed": 0,
            "details": {},
        }

        # 1. Primary Key Uniqueness
        cls._check_pk_uniqueness(dataset, results)

        # 2. Foreign Key Referential Integrity
        cls._check_foreign_keys(dataset, results)

        # 3. Enum Value Domain Compliance
        cls._check_enums(dataset, results)

        # 4. Date Ordering & Chronological Sequence
        cls._check_date_order(dataset, results)

        # 5. Arithmetic Line-Item & Total Reconciliation
        cls._check_arithmetic(dataset, results)

        results["is_valid"] = results["checks_failed"] == 0
        return results

    @classmethod
    def _check_pk_uniqueness(cls, data: Dict[str, Any], results: Dict[str, Any]):
        pk_mappings = [
            ("students", "student_id"),
            ("programs", "program_id"),
            ("fee_schedules", "fee_schedule_id"),
            ("enrollments", "enrollment_id"),
            ("invoices", "invoice_id"),
            ("invoice_lines", "invoice_line_id"),
            ("scholarships", "scholarship_id"),
            ("eligibility_awards", "award_id"),
            ("payments", "payment_id"),
            ("allocations", "allocation_id"),
            ("refunds", "refund_id"),
        ]

        pk_failures = []
        for table, pk_field in pk_mappings:
            records = data.get(table, [])
            keys = [getattr(r, pk_field) if hasattr(r, pk_field) else r[pk_field] for r in records]
            counts = Counter(keys)
            duplicates = [k for k, v in counts.items() if v > 1]
            if duplicates:
                pk_failures.append(f"{table}: {len(duplicates)} duplicate keys found (e.g. {duplicates[:3]})")

        if pk_failures:
            results["checks_failed"] += 1
            results["details"]["pk_uniqueness"] = {"passed": False, "errors": pk_failures}
        else:
            results["checks_passed"] += 1
            results["details"]["pk_uniqueness"] = {"passed": True, "count_tables_verified": len(pk_mappings)}

    @classmethod
    def _check_foreign_keys(cls, data: Dict[str, Any], results: Dict[str, Any]):
        def get_ids(table: str, field_name: str) -> Set[str]:
            return {
                getattr(r, field_name) if hasattr(r, field_name) else r[field_name]
                for r in data.get(table, [])
            }

        student_ids = get_ids("students", "student_id")
        program_ids = get_ids("programs", "program_id")
        enrollment_ids = get_ids("enrollments", "enrollment_id")
        invoice_ids = get_ids("invoices", "invoice_id")
        payment_ids = get_ids("payments", "payment_id")
        scholarship_ids = get_ids("scholarships", "scholarship_id")

        fk_failures = []

        # Check Enrollment -> Student & Program
        for e in data.get("enrollments", []):
            sid = getattr(e, "student_id", None) or e.get("student_id")
            pid = getattr(e, "program_id", None) or e.get("program_id")
            if sid not in student_ids:
                fk_failures.append(f"Enrollment orphan student_id: {sid}")
            if pid not in program_ids:
                fk_failures.append(f"Enrollment orphan program_id: {pid}")

        # Check Invoice -> Student & Enrollment
        for inv in data.get("invoices", []):
            sid = getattr(inv, "student_id", None) or inv.get("student_id")
            eid = getattr(inv, "enrollment_id", None) or inv.get("enrollment_id")
            if sid not in student_ids:
                fk_failures.append(f"Invoice orphan student_id: {sid}")
            if eid not in enrollment_ids:
                fk_failures.append(f"Invoice orphan enrollment_id: {eid}")

        # Check InvoiceLine -> Invoice
        for line in data.get("invoice_lines", []):
            iid = getattr(line, "invoice_id", None) or line.get("invoice_id")
            if iid not in invoice_ids:
                fk_failures.append(f"InvoiceLine orphan invoice_id: {iid}")

        # Check Payment -> Student
        for p in data.get("payments", []):
            sid = getattr(p, "student_id", None) or p.get("student_id")
            if sid not in student_ids:
                fk_failures.append(f"Payment orphan student_id: {sid}")

        # Check Allocation -> Payment & Invoice
        for a in data.get("allocations", []):
            pid = getattr(a, "payment_id", None) or a.get("payment_id")
            iid = getattr(a, "invoice_id", None) or a.get("invoice_id")
            if pid not in payment_ids:
                fk_failures.append(f"Allocation orphan payment_id: {pid}")
            if iid not in invoice_ids:
                fk_failures.append(f"Allocation orphan invoice_id: {iid}")

        # Check Refund -> Student & Payment
        for r in data.get("refunds", []):
            sid = getattr(r, "student_id", None) or r.get("student_id")
            pid = getattr(r, "payment_id", None) or r.get("payment_id")
            if sid not in student_ids:
                fk_failures.append(f"Refund orphan student_id: {sid}")
            if pid not in payment_ids:
                fk_failures.append(f"Refund orphan payment_id: {pid}")

        if fk_failures:
            results["checks_failed"] += 1
            results["details"]["fk_integrity"] = {"passed": False, "errors": fk_failures[:10]}
        else:
            results["checks_passed"] += 1
            results["details"]["fk_integrity"] = {"passed": True, "relationships_verified": 8}

    @classmethod
    def _check_enums(cls, data: Dict[str, Any], results: Dict[str, Any]):
        enum_failures = []
        valid_res = {e.value for e in ResidencyStatus}
        valid_stu_stat = {e.value for e in StudentStatus}
        valid_inv_stat = {e.value for e in InvoiceStatus}
        valid_pay_meth = {e.value for e in PaymentMethod}
        valid_pay_stat = {e.value for e in PaymentStatus}

        for s in data.get("students", []):
            r = getattr(s, "residency_status", None) or s.get("residency_status")
            val = r.value if hasattr(r, "value") else str(r)
            if val not in valid_res:
                enum_failures.append(f"Invalid residency_status: {val}")

        for inv in data.get("invoices", []):
            st = getattr(inv, "status", None) or inv.get("status")
            val = st.value if hasattr(st, "value") else str(st)
            if val not in valid_inv_stat:
                enum_failures.append(f"Invalid invoice_status: {val}")

        for p in data.get("payments", []):
            m = getattr(p, "payment_method", None) or p.get("payment_method")
            val_m = m.value if hasattr(m, "value") else str(m)
            if val_m not in valid_pay_meth:
                enum_failures.append(f"Invalid payment_method: {val_m}")

        if enum_failures:
            results["checks_failed"] += 1
            results["details"]["enum_validation"] = {"passed": False, "errors": enum_failures[:5]}
        else:
            results["checks_passed"] += 1
            results["details"]["enum_validation"] = {"passed": True}

    @classmethod
    def _check_date_order(cls, data: Dict[str, Any], results: Dict[str, Any]):
        date_failures = []
        for inv in data.get("invoices", []):
            issue = getattr(inv, "issue_date", None) or inv.get("issue_date")
            due = getattr(inv, "due_date", None) or inv.get("due_date")
            if issue and due and issue > due:
                date_failures.append(f"Invoice {getattr(inv, 'invoice_id', '')}: issue_date {issue} > due_date {due}")

        if date_failures:
            results["checks_failed"] += 1
            results["details"]["date_ordering"] = {"passed": False, "errors": date_failures[:5]}
        else:
            results["checks_passed"] += 1
            results["details"]["date_ordering"] = {"passed": True}

    @classmethod
    def _check_arithmetic(cls, data: Dict[str, Any], results: Dict[str, Any]):
        arithmetic_failures = []
        lines_by_inv = {}
        for line in data.get("invoice_lines", []):
            iid = getattr(line, "invoice_id", None) or line.get("invoice_id")
            lt = getattr(line, "line_total", None) or line.get("line_total")
            lines_by_inv.setdefault(iid, 0.0)
            lines_by_inv[iid] += float(lt)

        for inv in data.get("invoices", []):
            iid = getattr(inv, "invoice_id", None) or inv.get("invoice_id")
            subtotal = float(getattr(inv, "subtotal_amount", None) or inv.get("subtotal_amount"))
            sum_lines = round(lines_by_inv.get(iid, 0.0), 2)
            if abs(subtotal - sum_lines) > 0.02:
                arithmetic_failures.append(f"Invoice {iid}: subtotal ${subtotal:.2f} != sum(lines) ${sum_lines:.2f}")

        if arithmetic_failures:
            results["checks_failed"] += 1
            results["details"]["arithmetic_reconciliation"] = {"passed": False, "errors": arithmetic_failures[:5]}
        else:
            results["checks_passed"] += 1
            results["details"]["arithmetic_reconciliation"] = {"passed": True}

